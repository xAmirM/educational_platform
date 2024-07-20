from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from typing import Optional
import uuid
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    

    class Config:
        env_file = ".env"

settings = Settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    
def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expieres_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expieres_delta:
        expire = datetime.now() + expieres_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token):
    payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
    return payload


def generate_id():
    return str(uuid.uuid4())


def is_admin(user):
    if user["rank"] == "admin":
        return True
    return False