from fastapi import APIRouter, Depends, HTTPException
from dependancies import get_current_user
from database import database
from pydantic import BaseModel
import uuid
from relationship_ai import call_character_response

router = APIRouter()

class Message(BaseModel):
    message: str

@router.get("/{life_id}/relationships/{relationship_id}/messages")
async def get_messages(life_id: str, relationship_id: str):
    messages_list = await database.fetch_all(
        "SELECT id, sent_by_whom, message FROM messages WHERE relationship_id = :relationship_id ORDER BY created_at ASC",
        {"relationship_id": relationship_id}
    )
    return {"messages": [dict(r) for r in messages_list]}


@router.post("/{life_id}/relationships/{relationship_id}/messages")
async def generate_message(body: Message, life_id: str, relationship_id: str, user = Depends(get_current_user)):
    credits = await database.fetch_one(
        "Select credits from users where id = :id",
        {"id": user.id}
    )

    if credits["credits"]<1:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    relationship_stats = await database.fetch_one(
        "Select character_name, strength_number, relationship_type, openai_conversation_id from relationships where id = :id",
        {"id": relationship_id}
    )

    strength_number = relationship_stats["strength_number"]
    relationship_type = relationship_stats["relationship_type"]
    character_name = relationship_stats["character_name"]
    conv_id = relationship_stats["openai_conversation_id"]
    if not conv_id:
        raise HTTPException(status_code=500, detail="Conversation not initialized for this relationship")

    await database.execute(
        "INSERT INTO messages (id, relationship_id, sent_by_whom, message) VALUES (:id, :relationship_id, :sent_by_whom, :message)",
        {
            "id": str(uuid.uuid4()),
            "relationship_id": relationship_id,
            "sent_by_whom": "player",
            "message": body.message
        }
    )

    life_stats = await database.fetch_one(
        "SELECT rolling_summary FROM lives WHERE id = :id",
        {"id": life_id}
    )

    parsed = await call_character_response(
        conv_id,
        body.message,
        character_name,
        relationship_type,
        strength_number,
        life_stats["rolling_summary"],
    )

    your_response = parsed["your_response"]
    update_to_relationship_strength = parsed["update_to_relationship_strength"]
    new_relationship_type = parsed["new_relationship_type"]
    update_to_happiness = parsed["update_to_happiness"]

    await database.execute(
        "Insert into messages (id, relationship_id, sent_by_whom, message) values (:id, :relationship_id, :sent_by_whom, :message)",
        {"id": str(uuid.uuid4()),
        "relationship_id": relationship_id,
        "sent_by_whom": "other_person",
        "message": your_response}
    )

    await database.execute(
        "UPDATE lives SET happiness = happiness + :update_to_happiness where id = :id",
        {
            "id": life_id,
            "update_to_happiness": update_to_happiness
        }
    )

    if new_relationship_type:
        await database.execute(
            "UPDATE relationships SET strength_number = strength_number + :update_to_relationship_strength, relationship_type = :new_relationship_type WHERE id = :id",
            {"id": relationship_id,
            "update_to_relationship_strength": update_to_relationship_strength,
            "new_relationship_type": new_relationship_type}
        )
    else:
        await database.execute(
            "UPDATE relationships SET strength_number = strength_number + :update_to_relationship_strength WHERE id = :id",
            {"id": relationship_id, "update_to_relationship_strength": update_to_relationship_strength}
        )

    await database.execute(
        "UPDATE users set credits = credits -1 where id = :id",
        {"id": str(user.id)}
    )

    return {
        "response": your_response,
        "update_to_relationship_strength": update_to_relationship_strength,
        "update_to_relationship_type": new_relationship_type,
        "update_to_happiness": update_to_happiness,
        "relationship_type": relationship_type,
    }


@router.patch("/{life_id}/relationships/{relationship_id}/messages")
async def set_unread_to_zero(life_id: str, relationship_id: str, user = Depends(get_current_user)):
    unread_message_count = await database.fetch_one(
       "Select unread_message_count from relationships where id = :id",
        {"id": relationship_id}
    )
    unread_message_count = unread_message_count["unread_message_count"]
    if unread_message_count>0:
        await database.execute(
            "UPDATE lives SET unread_message_count = unread_message_count - :unread_message_count WHERE id = :life_id",
            {
                "unread_message_count": unread_message_count,
                "life_id": life_id
            }
        )
        await database.execute(
            "UPDATE relationships SET unread_message_count = 0 WHERE id = :relationship_id",
            {"relationship_id": relationship_id}
        )
    return {"status": "success"}
