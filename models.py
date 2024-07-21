from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    username: str
    phone_number: str
    password: str
    email: EmailStr

class UserInDB(BaseModel):
    username: str
    phone_number: str
    id: str
    email: EmailStr
    balance: int = 0
    items_owned: list = Field(default_factory=list)
    shopping_cart: list = Field(default_factory=list)
    hashed_password: str

class ShownUser(BaseModel):
    username: str 
    phone_number: int
    email: EmailStr
    rank: str = "student"



class Token(BaseModel):
    access_token: str
    token_type: str
 

class TokenData(BaseModel):
    user_id: str


class Item(BaseModel):
    name: str
    tag: str
    price: int


class DiscountCode(BaseModel):
    name: str
    expiery_seconds: int
    percentage: int = Field(le=100)
