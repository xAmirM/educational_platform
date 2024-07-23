from fastapi import FastAPI, Depends, HTTPException, status, Body
from models import User, UserInDB, TokenData, Token, ShownUser, Item, DiscountCode
from database import user_model, item_model, discount_code_model
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from utility import create_access_token, get_password_hash, verify_password, decode_access_token, generate_id, is_admin 
from jwt import InvalidTokenError

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
def home():
    return "Hello, world!"


@app.post("/register")
def register(user: User) -> ShownUser:
    
    user_data = user.dict()
    user_id = generate_id()

    id_taken = user_model.get_by_id(_id=user_id)

    while id_taken == user_id:
        user_id = generate_id()
    
    user_data.update({"_id": user_id})
    user_data.update({"shopping_cart": []})
    user_data.update({"items_owned": []})
    user_data.update({"rank": "student"})
    user_data.update({"balance": 0})

# THIS LINE IS TEMPORRARY AND WILL BE REMOVED
    if user_data["username"] == "admin":
        user_data.update({"rank": "admin"})

    password = user_data["password"]
    user_data.update({"hashed_password": get_password_hash(password)})
    user_data.pop("password")
    result = user_model.create(user_data)
    if result:
        return user_data

@app.get("/items")
def read_items() -> list:
        items = item_model.get_item_list()
        return items


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> ShownUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)    
        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception
        token_data = TokenData(user_id = user_id)
    except InvalidTokenError:
        raise credentials_exception
    user = user_model.get_by_id(token_data.user_id)
    if not user:
        raise credentials_exception
    return user
    

@app.get("/users/me")
def read_users_me(current_user: Annotated[str, Depends(get_current_user)]) -> ShownUser:
    return current_user


@app.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user_dict = user_model.get_by_username(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user_dict["id"] = user_dict.pop("_id")
    user = UserInDB(**user_dict)

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.id})

    return Token(access_token= access_token, token_type="bearer")


@app.post("/items/add")
def add_item(item: Item, current_user: Annotated[str, Depends(get_current_user)]):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user is not an admin")
    
    item_name = item.name
    result = item_model.get_by_name(item_name)
    if result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=" duplicated item name")

    item_data = item.dict()
    item_id = generate_id()

    id_taken = item_model.get_by_id(_id=item_id)

    while id_taken == item_id:
        item_id = user_model.generate_id()

    item_data["_id"] = item_id

    result = item_model.create(item_data)
    if result:
        return item_data


@app.put("/users/set/admin")
def set_admin(current_user: Annotated[str, Depends(get_current_user)], new_admin_id: str) -> ShownUser:
    if current_user["rank"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "user is not an admin")

    new_admin = user_model.get_by_id(new_admin_id)
    if not new_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    update = {"rank": "admin"}
    user_model.update(new_admin_id, update)

    user = user_model.get_by_id(new_admin_id)

    return user


def confirm_payment():
    return True


@app.post("/charge/balance")
def charge_balance(current_user: Annotated[str, Depends(get_current_user)], confirm: Annotated[bool, Depends(confirm_payment)], amount: int):
    if not confirm:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="payment failed")

    current_balance = current_user["balance"]

    new_balance = current_balance + amount
    user_model.update(current_user["_id"], {"balance": new_balance})
    return {"balance": new_balance}


@app.post("/shopping_cart/{act}/{item_name}")
def change_shopping_cart(current_user: Annotated[str, Depends(get_current_user)], act: str, item_name:str, existing_items: Annotated[list, Depends(read_items)]):
    if act not in ("add", "remove"):
        raise HTTPException(status=status.HTTP_404_NOT_FOUND, detail="path act argument is not add or remove")
    if act == "remove":
        if item_name in current_user["shopping_cart"]:
            shopping_cart: list = current_user["shopping_cart"]
            shopping_cart.remove(item_name)
            current_user["shopping_cart"] = shopping_cart
            user_model.update(current_user["_id"], {"shopping_cart": current_user["shopping_cart"]})
            return {"description": f"{item_name} removed", "shopping_cart": shopping_cart}
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user does not have this item")
            
    if act == "add":
        if not item_name in existing_items:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="item does not exist")
        if item_name in current_user["shopping_cart"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="item already exists in shopping cart")
        if item_name in current_user["items_owned"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="already owns this item")
        shopping_cart: list = current_user["shopping_cart"]
        shopping_cart.append(item_name)
        user_model.update(current_user["_id"], {"shopping_cart": shopping_cart})
        return {"description":"item added successfully", "shopping_cart": shopping_cart}
    

@app.post("/payoff/")
def payoff_shopping_cart(current_user: Annotated[str, Depends(get_current_user)], discount_code: str = Body(default=None)):
    total_price = 0
    discount_multiplier = 1
    if not current_user["shopping_cart"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="empty shopping cart")
    
    if discount_code and discount_code_model.is_useable(discount_code):
        code_data = discount_code_model.get_by_code(discount_code)
        percentage = code_data["percentage"]
        # math to get multiplier
        discount_multiplier = (100 - percentage)/100
    
    if not discount_code_model.is_useable(discount_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="discount code is not valid")

    for item in current_user["shopping_cart"]:
        item_price = item_model.get_by_name(item)["price"] * discount_multiplier
        total_price += item_price

    if current_user["balance"] < total_price:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not enough balance")

    new_balance = current_user["balance"] - total_price
    for item in current_user["shopping_cart"]:
        current_user["items_owned"].append(item)
    current_user["shopping_cart"] = []

    user_model.update(current_user["_id"], {"shopping_cart": current_user["shopping_cart"], "balance": new_balance, "items_owned":current_user["items_owned"]}, )
    return {"items_owned":current_user["items_owned"], "balance":new_balance}


@app.post("/discount/add/")
def discount_adder(code:DiscountCode, current_user: Annotated[str, Depends(get_current_user)]):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user is not an admin")
    result = discount_code_model.get_by_code(code.name)
    if result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="code already exists")
    discount_code_model.create(code.name, code.expiery_seconds, code.percentage)
    return {"code": code.name}


@app.put("/discount/remove/{code}")
def discount_remover(code: str, current_user: Annotated[str, Depends(get_current_user)]):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user is not an admin")
    deleted = discount_code_model.delete(code)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="code does not exist")
    return {"description": f"code {code} removed"}

        