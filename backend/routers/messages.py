from fastapi import APIRouter, Depends, HTTPException
from dependancies import get_current_user
from database import database
from pydantic import BaseModel
import uuid
from relationship_ai import call_character_response, init_relationship_conversation

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
        "Select character_name, strength_number, relationship_type, openai_conversation_id, pending_world_update from relationships where id = :id",
        {"id": relationship_id}
    )

    strength_number = relationship_stats["strength_number"]
    relationship_type = relationship_stats["relationship_type"]
    character_name = relationship_stats["character_name"]
    pending_world_update = relationship_stats["pending_world_update"]
    conv_id = relationship_stats["openai_conversation_id"]
    if not conv_id:
        await init_relationship_conversation(relationship_id)
        refreshed = await database.fetch_one(
            "SELECT openai_conversation_id FROM relationships WHERE id = :id",
            {"id": relationship_id},
        )
        conv_id = refreshed["openai_conversation_id"]

    await database.execute(
        "INSERT INTO messages (id, relationship_id, sent_by_whom, message) VALUES (:id, :relationship_id, :sent_by_whom, :message)",
        {
            "id": str(uuid.uuid4()),
            "relationship_id": relationship_id,
            "sent_by_whom": "player",
            "message": body.message
        }
    )

    parsed = await call_character_response(
        conv_id,
        body.message,
        character_name,
        relationship_type,
        strength_number,
        pending_world_update,
    )

    your_response = parsed["your_response"]
    update_to_relationship_strength = parsed["update_to_relationship_strength"]
    new_relationship_type = parsed["new_relationship_type"]
    update_to_happiness = parsed["update_to_happiness"]
    scenario_update = parsed["scenario_update"]

    await database.execute(
        "Insert into messages (id, relationship_id, sent_by_whom, message) values (:id, :relationship_id, :sent_by_whom, :message)",
        {"id": str(uuid.uuid4()),
        "relationship_id": relationship_id,
        "sent_by_whom": "other_person",
        "message": your_response}
    )

    await database.execute(
        "UPDATE lives SET happiness = LEAST(100, GREATEST(0, happiness + :update_to_happiness)) where id = :id",
        {
            "id": life_id,
            "update_to_happiness": update_to_happiness
        }
    )

    if scenario_update:
        line = f"- [{character_name} ({relationship_type})] {scenario_update}\n"
        await database.execute(
            "UPDATE lives SET character_texting_updates = character_texting_updates || :line WHERE id = :id",
            {"id": life_id, "line": line},
        )

    if pending_world_update:
        await database.execute(
            "UPDATE relationships SET pending_world_update = NULL WHERE id = :id",
            {"id": relationship_id},
        )

    if new_relationship_type:
        await database.execute(
            "UPDATE relationships SET strength_number = strength_number + :update_to_relationship_strength, relationship_type = :new_relationship_type WHERE id = :id",
            {"id": relationship_id,
            "update_to_relationship_strength": update_to_relationship_strength,
            "new_relationship_type": new_relationship_type}
        )
    elif update_to_relationship_strength:
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
