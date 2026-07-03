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
    "and scenario_update (string, only if this exchange is significant for the main character's life story — "
    "one sentence summary for the scenario engine; otherwise omit)"
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
    pending_world_update=None,
):
    instructions = (
        f"You are {character_name}, the main character's {relationship_type}. "
        f"Your relationship strength with them is {strength_number}/100. "
        f"You are texting them in a life simulation game. Stay in character. "
        f"new_relationship_type only describes YOUR bond with the main character, not their relationships with other people. "
        f"{JSON_INSTRUCTION}"
    )

    if pending_world_update:
        user_input = (
            f"[Private life update — player cannot see this] {pending_world_update}\n\n"
            f"They texted you: {user_input}"
        )

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
    scenario_update = data.get("scenario_update")
    return {
        "your_response": data["your_response"],
        "update_to_relationship_strength": data.get("update_to_relationship_strength", 0),
        "new_relationship_type": data.get("new_relationship_type"),
        "update_to_happiness": data.get("update_to_happiness", 0),
        "scenario_update": scenario_update if scenario_update else None,
    }
