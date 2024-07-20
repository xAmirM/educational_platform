from fastapi import FastAPI, Depends, HTTPException, status
from inputs import User, UserInDB, TokenData, Token, ShownUser, Item
from models import user_model, item_model
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

    password = user_data["password"]
    user_data.update({"hashed_password": get_password_hash(password)})
    user_data.pop("password")
    result = user_model.create(user_data)
    if result:
        return user_data

@app.get("/items")
def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
        return {"token": token}


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