from fastapi import APIRouter, Depends, HTTPException
from dependancies import get_current_user
from database import database
from pydantic import BaseModel
from openai import AsyncOpenAI
import json
import uuid

client = AsyncOpenAI()
router = APIRouter()

class Message(BaseModel):
    message: str

@router.get("/{life_id}/relationships")
async def get_relationships(life_id: str):
    relationships_list = await database.fetch_all(
        "SELECT id, character_name, strength_number, relationship_type, unread_message_count FROM relationships WHERE life_id = :life_id ORDER BY unread_message_count DESC",
        {"life_id": life_id}
    )
    return {"relationships": [dict(r) for r in relationships_list]}

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
    
    happiness = await database.fetch_one(
        "Select happiness from lives where id = :id",
        {"id": life_id}
    )
    happiness = happiness["happiness"]

    relationship_stats = await database.fetch_one(
        "Select strength_number, relationship_type, rolling_summary from relationships where id = :id",
        {"id": relationship_id}
    )

    rolling_summary = relationship_stats["rolling_summary"]
    strength_number = relationship_stats["strength_number"]
    relationship_type = relationship_stats["relationship_type"]
    rolling_summary = relationship_stats["rolling_summary"]


    messages_list = await database.fetch_all(
        "SELECT sent_by_whom, message FROM messages WHERE relationship_id = :relationship_id ORDER BY created_at DESC LIMIT 3",
        {"relationship_id": relationship_id}
    )

    player_message_id = str(uuid.uuid4())
    await database.execute(
        "INSERT INTO messages (id, relationship_id, sent_by_whom, message) VALUES (:id, :relationship_id, :sent_by_whom, :message)",
        {
            "id": player_message_id,
            "relationship_id": relationship_id,
            "sent_by_whom": "player",
            "message": body.message
        }
    )


    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are the main character's {relationship_type}. Here is a summary of your relationship: {rolling_summary} with relationship strength {strength_number}/100. Here are your past three messages: {messages_list}"},
            {"role": "user", "content": f"They just sent you the message {body.message}. Return JSON only with fields: your_response (string), updated_rolling_summary (string, only if needed), update_to_relationship_strength (int), update_to_happiness (int), and new_relationship_type (string, only if the relationship status changed)"}
        ],
        response_format={"type": "json_object"}
    )
    response = completion.choices[0].message.content
    response = json.loads(response)
    print("RESPONSE:", response)
    your_response = response["your_response"]
    update_to_relationship_strength = response.get("update_to_relationship_strength") or response.get("delta update_to_relationship_strength", 0)
    new_relationship_type = response.get("new_relationship_type") or response.get("update_to_new_relationship_type")
    update_to_happiness = response.get("update_to_happiness") or response.get("delta update_to_happiness", 0)
    new_rolling_summary = response.get("updated_rolling_summary") or rolling_summary


    id = str(uuid.uuid4())
    await database.execute(
        "Insert into messages (id, relationship_id, sent_by_whom, message) values (:id, :relationship_id, :sent_by_whom, :message)",
        {"id": id,
        "relationship_id": relationship_id, 
        "sent_by_whom": "other_person",
        "message": your_response
        }
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
                "UPDATE relationships SET strength_number = strength_number + :update_to_relationship_strength, relationship_type = :new_relationship_type, rolling_summary = :rolling_summary WHERE id = :id",
                {"id": relationship_id,
                "update_to_relationship_strength": update_to_relationship_strength,
                "new_relationship_type": new_relationship_type,
                "rolling_summary": new_rolling_summary}
            )
    else:
        await database.execute(
            "UPDATE relationships SET strength_number = strength_number + :update_to_relationship_strength, rolling_summary = :rolling_summary WHERE id = :id",
            {"id": relationship_id, "update_to_relationship_strength": update_to_relationship_strength,  "rolling_summary": new_rolling_summary}
        )

    await database.execute(
        "UPDATE users set credits = credits -1 where id = :id",
        {"id": str(user.id)}
    )


    updated_stats = await database.fetch_one(
        "SELECT strength_number, relationship_type FROM relationships WHERE id = :id",
        {"id": relationship_id}
    )

    return {
        "response": your_response,
        "update_to_relationship_strength": update_to_relationship_strength,
        "update_to_relationship_type": new_relationship_type,
        "update_to_happiness": update_to_happiness,
        "relationship_type": updated_stats["relationship_type"],
        "strength_number": updated_stats["strength_number"],
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
