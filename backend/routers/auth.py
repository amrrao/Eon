from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase_client import supabase
from database import database
from dependancies import get_current_user
from fastapi import Depends


router = APIRouter()


class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password:str


@router.post("/signup")
async def signup(body: SignupRequest):
    response = supabase.auth.sign_up(
        {
            "email": body.email,
            "password": body.password,  
        }
    )
    if response.user is None:
        raise HTTPException(status_code=400, detail="Signup failed")
    
    await database.execute(
        "Insert into users (id, email) values (:id, :email)",
        {"id": str(response.user.id), "email": body.email}
    )
    return {"token": response.session.access_token}



@router.post("/login")
def login(body: LoginRequest):
    response = supabase.auth.sign_in_with_password(
    {
        "email": body.email,
        "password": body.password,
    }
    )
    if response.user is None:
        raise HTTPException(status_code=400, detail="Invalid Credentials")

    return {"token": response.session.access_token}
