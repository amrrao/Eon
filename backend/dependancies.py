from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from supabase_client import supabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        response = supabase.auth.get_user(token)
        if not response.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")