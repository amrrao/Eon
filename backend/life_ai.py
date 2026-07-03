from openai import AsyncOpenAI
import json
from database import database

client = AsyncOpenAI()
MODEL = "gpt-4o-mini"
COMPACT_THRESHOLD = 15000


async def init_life_conversation(life_id):
    conv = await client.conversations.create()
    await database.execute(
        "UPDATE lives SET openai_life_conversation_id = :conv_id WHERE id = :id",
        {"conv_id": conv.id, "id": life_id},
    )


async def call_life_response(
    life_id,
    user_input,
    age,
    money,
    happiness,
    intelligence,
    reputation,
    relationships_list,
    character_texting_updates="",
):
    row = await database.fetch_one(
        "SELECT openai_life_conversation_id FROM lives WHERE id = :id",
        {"id": life_id},
    )
    conv_id = row["openai_life_conversation_id"]
    if not conv_id:
        raise ValueError("Life conversation not initialized")

    if age < 6:
        age_context = "The main character is a young child (0-5). Scenarios must fit early childhood — family, home, nothing age-inappropriate."
    elif age < 13:
        age_context = "The main character is a child (6-12). Scenarios involve school, friends, and family."
    elif age < 18:
        age_context = "The main character is a teenager (13-17). Scenarios involve high school, identity, romance, and peer pressure."
    else:
        age_context = "The main character is an adult (18+). Scenarios involve work, college, money, romance, and independence."

    cast = ", ".join(relationships_list) if relationships_list else "none yet"
    instructions = (
        "You are a dramatic life simulator game engine. Generate tense scenarios with real stakes. "
        "Write in second person. Only use named characters from the existing relationships list "
        "unless adding new people via new_relationships. "
        f"{age_context}"
    )

    input_text = (
        f"Age: {age}. Stats: ${money}, happiness {happiness}/100, "
        f"intelligence {intelligence}/100, reputation {reputation}/100.\n"
        f"Existing relationships: {cast}.\n"
    )
    if character_texting_updates:
        input_text += f"Updates from character texting since last event:\n{character_texting_updates}\n"
    input_text += f"{user_input}\n\nRespond in JSON."

    response = await client.responses.create(
        model=MODEL,
        conversation={"id": conv_id},
        instructions=instructions,
        input=input_text,
        store=True,
        context_management=[{"type": "compaction", "compact_threshold": COMPACT_THRESHOLD}],
        text={"format": {"type": "json_object"}},
    )

    return json.loads(response.output_text)
