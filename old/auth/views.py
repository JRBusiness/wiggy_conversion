from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

router = APIRouter()

# Configure authentication
SECRET_KEY = "your-secret-key"  # Replace with a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class User(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str


# Simulated user data (replace with actual database queries)
fake_users_db = {
    "user1": {
        "id": 1,
        "username": "user1",
        "email": "user1@example.com",
        "password_hash": "$2b$12$1wfusv5tPw6eW3gXwvqpgu3.nqfYP5lcYmbDxmcI3KkH1A9X7iQcG",  # "password"
    }
}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# Authenticate user
def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not pwd_context.verify(password, user["password_hash"]):
        return None
    return User(**user)


# Create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# User registration
def register_user(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password_hash)
    user_data = user.dict()
    user_data["password_hash"] = hashed_password
    fake_users_db[user.username] = user_data
    return user


# Auth token endpoint
@router.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Protected endpoint example
@router.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        if user := fake_users_db.get(username):
            return {
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
            }
        else:
            raise HTTPException(status_code=401, detail="User not found")
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=401, detail="Invalid authentication token"
        ) from e
