from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from supabase_client import supabase
from database import database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        response = supabase.auth.get_user(token)
        if not response.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")


async def require_life_owner(life_id: str, user) -> None:
    life = await database.fetch_one(
        "SELECT user_id FROM lives WHERE id = :id",
        {"id": life_id},
    )
    if not life or str(life["user_id"]) != str(user.id):
        raise HTTPException(status_code=404, detail="Life not found")
