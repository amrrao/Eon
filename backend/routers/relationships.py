from fastapi import APIRouter, Depends
from database import database
from dependancies import get_current_user, require_life_owner

router = APIRouter()

@router.get("/{life_id}/relationships")
async def get_relationships(life_id: str, user = Depends(get_current_user)):
    await require_life_owner(life_id, user)
    relationships_list = await database.fetch_all(
        "SELECT id, character_name, strength_number, relationship_type, unread_message_count FROM relationships WHERE life_id = :life_id ORDER BY unread_message_count DESC",
        {"life_id": life_id}
    )
    return {"relationships": [dict(r) for r in relationships_list]}
