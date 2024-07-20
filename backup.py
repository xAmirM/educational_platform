from fastapi import FastAPI, Depends, HTTPException, status
from models import User, UserInDB, TokenData, Token, ShownUser, Item
from database import user_model, item_model
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from utility import create_access_token, get_password_hash, verify_password, decode_access_token, generate_user_id 
from jwt import InvalidTokenError



app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
def home():
    return "Hello, world!"


@app.post("/register")
def register(user: User) -> ShownUser:
    
    user_data = user.dict()
    user_id = generate_user_id()

    id_taken = user_model.get_by_id(_id=user_id)

    while id_taken:
        user_id = user_model.get_by_id()
        id_taken = user_id
    
    user_data.update({"_id": user_id})
    password = user_data["password"]
    user_data.update({"hashed_password": get_password_hash(password)})
    user_data.pop("password")
    user = user_model.create(user_data)

    if user:
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
        username = payload.get("sub")

        if not username:
            raise credentials_exception
        token_data = TokenData(username = username)
    except InvalidTokenError:
        raise credentials_exception
    user = user_model.get_by_username(username = token_data.username)
    if not user:
        raise credentials_exception
    return user
    

@app.get("/users/me")
def read_users_me(current_user: Annotated[str, Depends(get_current_user)]) -> ShownUser:
     return current_user


@app.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = user_model.get_by_username(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})

    return Token(access_token= access_token, token_type="bearer")

from fastapi import FastAPI, Depends, HTTPException, status
from models import User, UserInDB, TokenData, Token, ShownUser, Item
from database import user_model, item_model
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from utility import create_access_token, get_password_hash, verify_password, decode_access_token, generate_user_id 
from jwt import InvalidTokenError



app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
def home():
    return "Hello, world!"


@app.post("/register")
def register(user: User) -> ShownUser:
    
    user_data = user.dict()
    user_id = generate_user_id()

    id_taken = user_model.get_by_id(_id=user_id)

    while id_taken:
        user_id = user_model.get_by_id()
        id_taken = user_id
    
    user_data.update({"_id": user_id})
    password = user_data["password"]
    user_data.update({"hashed_password": get_password_hash(password)})
    user_data.pop("password")
    user = user_model.create(user_data)

    if user:
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
        username = payload.get("sub")

        if not username:
            raise credentials_exception
        token_data = TokenData(username = username)
    except InvalidTokenError:
        raise credentials_exception
    user = user_model.get_by_username(username = token_data.username)
    if not user:
        raise credentials_exception
    return user
    

@app.get("/users/me")
def read_users_me(current_user: Annotated[str, Depends(get_current_user)]) -> ShownUser:
    return current_user


@app.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = user_model.get_by_username(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})

    return Token(access_token= access_token, token_type="bearer")

