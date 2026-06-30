from fastapi import APIRouter
from database import database

router = APIRouter()

@router.get("/{life_id}/relationships")
async def get_relationships(life_id: str):
    relationships_list = await database.fetch_all(
        "SELECT id, character_name, strength_number, relationship_type, unread_message_count FROM relationships WHERE life_id = :life_id ORDER BY unread_message_count DESC",
        {"life_id": life_id}
    )
    return {"relationships": [dict(r) for r in relationships_list]}
