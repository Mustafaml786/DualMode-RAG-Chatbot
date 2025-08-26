from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from db.database import get_db_session
from models.user import User, Session
from services.auth_service import hash_password, verify_password, generate_session_token
import uuid

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup", status_code=201)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db_session)):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_pw = hash_password(user_data.password)
    new_user = User(email=user_data.email, password_hash=hashed_pw)
    db.add(new_user)
    await db.commit()
    return {"message": "User created successfully"}

@router.post("/login")
async def login(user_data: UserLogin, response: Response, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalars().first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session_token = generate_session_token()
    new_session = Session(user_id=user.id, session_token=session_token)
    db.add(new_session)
    await db.commit()
    
    response.set_cookie(key="session_token", value=session_token, httponly=True)
    return {"message": "Login successful", "session_id": new_session.id}

@router.post("/logout")
async def logout(response: Response, db: AsyncSession = Depends(get_db_session)):
    # In a real app, you would get session_token from cookie/header to invalidate it
    response.delete_cookie("session_token")
    return {"message": "Logout successful"}