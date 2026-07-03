from openai import AsyncOpenAI
import json
from database import database

client = AsyncOpenAI()
MODEL = "gpt-4o-mini"
COMPACT_THRESHOLD = 15000

JSON_INSTRUCTION = (
    "Return JSON only with fields: your_response (string), "
    "update_to_relationship_strength (int), "
    "update_to_happiness (int), "
    "new_relationship_type (string, only if how YOU and the main character relate changed — "
    "e.g. friend to ex, acquaintance to dating; NOT for news about other people in their life; "
    "you are not engaged to them just because they told you someone else proposed; omit if unchanged), "
    "and updated_life_rolling_summary (string, only if this exchange is life-significant — "
    "e.g. confession, fight, breakup, betrayal, major secret, or romance milestone; "
    "rewrite the full life summary under 80 words to include what happened; otherwise omit)"
)


async def init_relationship_conversation(relationship_id, intro_message=None):
    if intro_message:
        conv = await client.conversations.create(
            items=[{"type": "message", "role": "assistant", "content": intro_message}]
        )
    else:
        conv = await client.conversations.create()

    await database.execute(
        "UPDATE relationships SET openai_conversation_id = :conv_id WHERE id = :id",
        {"conv_id": conv.id, "id": relationship_id},
    )


async def call_character_response(
    conv_id,
    user_input,
    character_name,
    relationship_type,
    strength_number,
    life_rolling_summary=None,
):
    instructions = (
        f"You are {character_name}, the main character's {relationship_type}. "
        f"Your relationship strength with them is {strength_number}/100. "
        f"You are texting them in a life simulation game. Stay in character. "
        f"new_relationship_type only describes YOUR bond with the main character, not their relationships with other people. "
        f"{JSON_INSTRUCTION}"
    )
    if life_rolling_summary:
        instructions += f"\nThe main character's life so far: {life_rolling_summary}"

    response = await client.responses.create(
        model=MODEL,
        conversation={"id": conv_id},
        instructions=instructions,
        input=f"{user_input}\n\nRespond in JSON.",
        store=True,
        context_management=[{"type": "compaction", "compact_threshold": COMPACT_THRESHOLD}],
        text={"format": {"type": "json_object"}},
    )

    data = json.loads(response.output_text)
    updated_life_rolling_summary = data.get("updated_life_rolling_summary")
    return {
        "your_response": data["your_response"],
        "update_to_relationship_strength": data.get("update_to_relationship_strength", 0),
        "new_relationship_type": data.get("new_relationship_type"),
        "update_to_happiness": data.get("update_to_happiness", 0),
        "updated_life_rolling_summary": updated_life_rolling_summary if updated_life_rolling_summary else None,
    }
