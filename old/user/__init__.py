from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.auth import oauth2_scheme

app = FastAPI()


# User Model
class User(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime


# Simulated user data (replace with actual database queries)
fake_users_db = [
    User(id=1, username="user1", email="user1@example.com", created_at=datetime.now()),
    User(id=2, username="user2", email="user2@example.com", created_at=datetime.now()),
    # Add more user data as needed
]


# Get current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    # Retrieve the user ID from the token and fetch the corresponding user from the database
    # Implement the logic here based on your requirements
    user = fake_users_db.get(token)  # Simulated database query
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# Protected endpoint to get current user
@app.get("/user/me")
async def get_current_user_route(current_user: User = Depends(get_current_user)):
    return current_user
