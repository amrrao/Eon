from fastapi import APIRouter, Depends, HTTPException
from dependancies import get_current_user
from database import database
from pydantic import BaseModel
from openai import AsyncOpenAI
import json
import uuid

client = AsyncOpenAI()
router = APIRouter()


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

