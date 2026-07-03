from fastapi import APIRouter, Depends, HTTPException
from dependancies import get_current_user
from database import database
from pydantic import BaseModel
from openai import AsyncOpenAI
import json
import uuid
from relationship_ai import init_relationship_conversation
from life_ai import init_life_conversation, call_life_response

client = AsyncOpenAI()
router = APIRouter()

class CreateLifeRequest(BaseModel):
    gender: str


class Decision(BaseModel):
    decision: str

@router.get("/")
async def get_all_lives(user = Depends(get_current_user)):
    lives = await database.fetch_all(
        "SELECT id, gender, age, created_at, is_active FROM lives WHERE user_id = :user_id AND alive = true ORDER BY is_active DESC, created_at DESC",
        {"user_id": str(user.id)}
    )
    return {"lives": [dict(l) for l in lives]}

@router.post("/")
async def create_life(body: CreateLifeRequest, user = Depends(get_current_user)):
    credits = await database.fetch_one(
        "Select credits from users where id = :id",
        {"id": user.id}
        )
    if credits["credits"]<1:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    life_id = str(uuid.uuid4())
    await database.execute(
        "UPDATE lives SET is_active = false WHERE user_id = :user_id",
        {"user_id": str(user.id)}
    )
    await database.execute(
        "Insert into lives (id, user_id, gender, unread_message_count) values (:id, :user_id, :gender, :unread_message_count)",
        {"id": life_id,
        "user_id": str(user.id), 
        "gender": body.gender,
        "unread_message_count": 0}
    )
    await init_life_conversation(life_id)

    life_data = await call_life_response(
        life_id,
        f"Generate a starting life scenario for a {body.gender} baby just born. "
        "Return JSON with fields: scenario (string), choices (array of 3 strings), "
        "mother_name (string), father_name (string).",
        age=0,
        money=0,
        happiness=50,
        intelligence=5,
        reputation=50,
        relationships_list=[],
    )
    mom_name = life_data["mother_name"]
    dad_name = life_data["father_name"]
    scenario = life_data["scenario"]
    choices = life_data["choices"]
    relationship_id_mom = str(uuid.uuid4())
    relationship_id_dad = str(uuid.uuid4())
    await database.execute(
        "Insert into relationships (id, life_id, character_name, strength_number, relationship_type, unread_message_count) values (:id, :life_id, :character_name, :strength_number, :relationship_type, :unread_message_count)",
        {"id": relationship_id_mom,
        "life_id": life_id, 
        "character_name": mom_name,
        "strength_number": 80,
        "relationship_type": "mother",
        "unread_message_count": 0}
    )
    await init_relationship_conversation(relationship_id_mom)
    await database.execute(
        "Insert into relationships (id, life_id, character_name, strength_number, relationship_type, unread_message_count) values (:id, :life_id, :character_name, :strength_number, :relationship_type, :unread_message_count)",
        {"id": relationship_id_dad,
        "life_id": life_id, 
        "character_name": dad_name,
        "strength_number": 80,
        "relationship_type": "father",
        "unread_message_count": 0}
    )
    await init_relationship_conversation(relationship_id_dad)
    event_id = str(uuid.uuid4())
    await database.execute(
        "Insert into events (id, life_id, scenario, possible_choices) values (:id, :life_id, :scenario, :possible_choices)",
        {"id": event_id,
        "life_id": life_id, 
        "scenario": scenario,
        "possible_choices": json.dumps(choices)}
    )
    await database.execute(
        "UPDATE users set credits = credits -1 where id = :id",
        {"id": str(user.id)}
    )

    return{
        "life_id": life_id,
        "event_id": event_id,
        "mother": mom_name,
        "father": dad_name,
        "scenario": scenario,
        "choices": choices,
    }




@router.delete("/{life_id}")
async def delete_life(life_id: str, user = Depends(get_current_user)):
    life = await database.fetch_one(
        "SELECT user_id FROM lives WHERE id = :id",
        {"id": life_id}
    )
    if not life or str(life["user_id"]) != str(user.id):
        raise HTTPException(status_code=404, detail="Life not found")

    await database.execute("DELETE FROM lives WHERE id = :id", {"id": life_id})
    return {"status": "success"}

@router.post("/{life_id}/events")
async def generate_event(life_id: str, user = Depends(get_current_user)):

    life_stats = await database.fetch_one(
        "Select rolling_summary, age, money, happiness, intelligence, reputation from lives where id = :id",
        {"id": life_id}
        )
    rolling_summary = life_stats["rolling_summary"]
    age = life_stats["age"]
    money = life_stats["money"]
    happiness = life_stats["happiness"]
    intelligence = life_stats["intelligence"]
    reputation = life_stats["reputation"]

    existing_relationships = await database.fetch_all(
        "SELECT character_name, relationship_type FROM relationships WHERE life_id = :life_id",
        {"life_id": life_id}
    )
    existing_names = [f"{r['character_name']} ({r['relationship_type']})" for r in existing_relationships]
    
    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are a chaotic, dramatic life simulator game engine. Your job is to generate "
                "scenarios that create genuine tension and force hard tradeoffs, not wholesome slice-of-life moments. "
                "Every scenario should put something at risk: a relationship, money, reputation, or a secret. "
                "Favor conflict, rivalry, temptation, and consequences over comfort and harmony. "
                "Think reality TV drama, not a parenting blog."
            )},
            {"role": "user", "content": (
            f"Life so far: {rolling_summary}\n"
            f"Stats: ${money}, happiness {happiness}/100, "
            f"intelligence {intelligence}/100, reputation {reputation}/100.\n\n"
            f"Existing relationships in this life: {', '.join(existing_names) if existing_names else 'none yet'}.\n\n"
            f"Generate the NEXT dramatic moment in this life. Something must be at stake. The scenario must be relevant to the current age {age}"
            f"IMPORTANT: Do not continue the same storyline from the rolling summary for more than 2 turns "
            f"in a row. If the rolling summary already covers an ongoing conflict, resolve it NOW in this "
            f"scenario, then pivot to a completely different area of life: romance, family secrets, money "
            f"trouble, identity, friendship betrayal, health, or ambition.\n\n"
            f"Favor scenarios about: romantic tension or jealousy, a friend betraying your trust, a family "
            f"member revealing something that changes how you see them, being caught in a lie, having to "
            f"choose between two people who both want something from you, discovering a secret that isn't "
            f"yours to know. Avoid generic competitions, contests, or external props as the source of drama — "
            f"the drama should come from how people in this life actually feel about each other.\n\n"
            f"DEFAULT: advance the age forward (by 1 or more years) after every single turn. "
            f"RARE EXCEPTION: only stay at the same age if this exact scenario creates a genuine cliffhanger "
            f"that demands immediate resolution before time can pass. This exception should happen no more "
            f"than 1 out of every 4 turns. If in doubt, advance the age.\n\n"
            f"Scenario: under 50 words, punchy, second person, no fluff or scene-setting filler.\n"
            f"Choices: 3 options that are genuinely different in risk/reward, not just flavor text — "
            f"one safe, one risky, one morally gray.\n\n"
            f"Return JSON only with fields: scenario (string), choices (array of 3 strings), "
            f"update_to_age (int), and new_relationships (array).\n\n"
            f"new_relationships is REQUIRED. It must be an empty array [] if the scenario only involves "
            f"people already listed above. If the scenario introduces ANY named person not already in the "
            f"existing relationships list, add one object per new person with: name_of_person (string), "
            f"relationship_type (string), relationship_strength (int 1-100), message_from_relationship "
            f"(string — a short text message they would send the player introducing themselves or reacting "
            f"to the scenario)."
        )}
        ],
        response_format={"type": "json_object"}
    )
    response = completion.choices[0].message.content
    life_data = json.loads(response)
    scenario = life_data["scenario"]
    choices = life_data["choices"]

    event_id = str(uuid.uuid4())
    await database.execute(
        "Insert into events (id, life_id, scenario, possible_choices) values (:id, :life_id, :scenario, :possible_choices)",
        {"id": event_id,
        "life_id": life_id, 
        "scenario": scenario,
        "possible_choices": json.dumps(choices)}
    )

    new_relationships = life_data.get("new_relationships", [])

    existing_character_names = {r["character_name"].lower() for r in existing_relationships}

    for person in new_relationships:
        name = person.get("name_of_person")
        if not name or name.lower() in existing_character_names:
            continue

        rel_id = str(uuid.uuid4())
        rel_type = person.get("relationship_type") or "acquaintance"
        rel_strength = person.get("relationship_strength") or 50
        intro_message = person.get("message_from_relationship")

        await database.execute(
            "Insert into relationships (id, life_id, character_name, strength_number, relationship_type, unread_message_count) values (:id, :life_id, :character_name, :strength_number, :relationship_type, :unread_message_count)",
            {"id": rel_id,
            "life_id": life_id,
            "character_name": name,
            "strength_number": rel_strength,
            "relationship_type": rel_type,
            "unread_message_count": 1}
        )
        await database.execute(
            "UPDATE lives SET unread_message_count = unread_message_count + 1 WHERE id = :id",
            {"id": life_id}
        )
        if intro_message:
            await database.execute(
                "Insert into messages (id, relationship_id, sent_by_whom, message) values (:id, :relationship_id, :sent_by_whom, :message)",
                {"id": str(uuid.uuid4()),
                "relationship_id": rel_id,
                "sent_by_whom": name,
                "message": intro_message}
            )
        await init_relationship_conversation(rel_id, intro_message)
        existing_character_names.add(name.lower())

    return {
        "event_id": event_id,
        "scenario": scenario,
        "choices": choices,
    }



@router.patch("/{life_id}/events/{event_id}")
async def update_choice(body: Decision, life_id: str, event_id: str, user = Depends(get_current_user)):
    credits = await database.fetch_one(
    "SELECT credits FROM users WHERE id = :id",
    {"id": user.id}
    )
    if credits["credits"] < 1:
        raise HTTPException(status_code=402, detail="Insufficient credits")
        
    life_stats = await database.fetch_one(
       "Select rolling_summary, age, money, happiness, intelligence, reputation from lives where id = :id",
        {"id": life_id}
        )
    rolling_summary = life_stats["rolling_summary"]
    age = life_stats["age"]
    money = life_stats["money"]
    happiness = life_stats["happiness"]
    intelligence = life_stats["intelligence"]
    reputation = life_stats["reputation"]

    event_stats = await database.fetch_one(
            "Select scenario from events where id = :id",
            {"id": event_id}
            )
    scenario = event_stats["scenario"]


    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are a chaotic, dramatic life simulator game engine. You are trying to make "
                "people playing this simulation get genuinely addicted to it through real stakes "
                "and consequences, not wholesome resolutions."
            )},
            {"role": "user", "content": (
                f"A user of age {age} with a life rolling summary: {rolling_summary}\n"
                f"Stats: ${money}, happiness {happiness}/100, intelligence {intelligence}/100, "
                f"reputation {reputation}/100.\n"
                f"They just made the choice to {body.decision} when asked: {scenario}\n\n"
                f"Write the consequence of this choice into the rolling summary. Be specific about "
                f"what changed — don't just restate the choice, show its real impact on relationships, "
                f"reputation, or circumstances. Keep the updated_rolling_summary under 80 words, "
                f"condensing or dropping older resolved details to make room for what just happened.\n\n"
                f"DEFAULT: advance the age forward (update_to_age = 1 or more). "
                f"RARE EXCEPTION: only keep the same age if this choice creates a cliffhanger requiring "
                f"immediate follow-up. This should happen no more than 1 out of every 4 turns. "
                f"If in doubt, advance the age.\n\n"
                f"Return JSON only with fields: updated_rolling_summary (string), "
                f"update_to_money (integer), update_to_intelligence (integer), "
                f"update_to_happiness (integer), update_to_reputation (integer), "
                f"update_to_age (integer). If a stat isn't relevant to this scenario, set its update to 0."
            )}
        ],
        response_format={"type": "json_object"}
    )
    response = completion.choices[0].message.content
    updates = json.loads(response)
    print("Updates:", updates)
    updated_rolling_summary = updates.get("updated_rolling_summary")
    update_to_money = updates.get("update_to_money", 0)
    update_to_intelligence = updates.get("update_to_intelligence", 0)
    update_to_happiness = updates.get("update_to_happiness", 0)
    update_to_reputation = updates.get("update_to_reputation", 0)
    update_to_age = updates.get("update_to_age", 0)
    
    await database.execute(
        "UPDATE events SET decided_choice = :decided_choice, update_to_money = :update_to_money, update_to_intelligence = :update_to_intelligence, update_to_happiness = :update_to_happiness, update_to_reputation = :update_to_reputation, update_to_age = :update_to_age WHERE id = :event_id",
        {
            "decided_choice": body.decision,
            "update_to_money": update_to_money,
            "update_to_intelligence": update_to_intelligence,
            "update_to_happiness": update_to_happiness,
            "update_to_reputation": update_to_reputation,
            "update_to_age": update_to_age,
            "event_id": event_id
        }
    )

    await database.execute(
        """UPDATE lives SET 
            money = money + :update_to_money, 
            intelligence = LEAST(100, GREATEST(0, intelligence + :update_to_intelligence)), 
            happiness = LEAST(100, GREATEST(0, happiness + :update_to_happiness)), 
            reputation = LEAST(100, GREATEST(0, reputation + :update_to_reputation)), 
            age = age + :update_to_age, 
            rolling_summary = :rolling_summary 
        WHERE id = :life_id""",
        {
            "update_to_money": update_to_money,
            "update_to_intelligence": update_to_intelligence,
            "update_to_happiness": update_to_happiness,
            "update_to_reputation": update_to_reputation,
            "update_to_age": update_to_age,
            "life_id": life_id,
            "rolling_summary": updated_rolling_summary
        }
    )

    await database.execute(
        "UPDATE users SET credits = credits - 1 WHERE id = :id",
        {"id": str(user.id)}
    )


    return {
        "status": "success",
        "money": money + update_to_money,
        "intelligence": max(0, min(100, intelligence + update_to_intelligence)),
        "happiness": max(0, min(100, happiness + update_to_happiness)),
        "reputation": max(0, min(100, reputation + update_to_reputation)),
        "age": age + update_to_age,
    }

@router.get("/active")
async def get_active_life(user = Depends(get_current_user)):
    life_stats = await database.fetch_one(
        "Select id, age, money, happiness, intelligence, reputation, alive from lives where user_id = :user_id order by is_active desc, created_at desc limit 1",
        {"user_id": str(user.id)}
    )
    if not life_stats:
        return {"life_id": None}
    age = life_stats["age"]
    money = life_stats["money"]
    happiness = life_stats["happiness"]
    intelligence = life_stats["intelligence"]
    reputation = life_stats["reputation"]
    alive = life_stats["alive"]
    life_id = life_stats['id']
    last_event = await database.fetch_one(
        "SELECT id, scenario, possible_choices, decided_choice FROM events WHERE life_id = :life_id ORDER BY created_at DESC LIMIT 1",
        {"life_id": life_id}
    )
    event_id = last_event["id"]
    scenario = last_event["scenario"]
    possible_choices = last_event["possible_choices"]
    decided_choice = last_event["decided_choice"]


    return{
        "life_id": life_id,
        "event_id": event_id,
        "age": age,
        "money": money,
        "happiness": happiness,
        "intelligence": intelligence,
        "reputation": reputation,
        "alive": alive,
        "scenario": scenario,
        "possible_choices": possible_choices,
        "decided_choice": decided_choice
    }



@router.patch("/{life_id}/activate")
async def activate_life(life_id: str, user = Depends(get_current_user)):
    await database.execute(
        "UPDATE lives SET is_active = false WHERE user_id = :user_id",
        {"user_id": str(user.id)}
    )
    await database.execute(
        "UPDATE lives SET is_active = true WHERE id = :id",
        {"id": life_id}
    )
    return {"status": "success"}


@router.get("/{life_id}")
async def get_life(life_id: str):

    life_stats = await database.fetch_one(
        "Select age, money, happiness, intelligence, reputation, alive from lives where id = :id",
        {"id": life_id}
        )

    if not life_stats:
        return {"life_id": None}
    age = life_stats["age"]
    money = life_stats["money"]
    happiness = life_stats["happiness"]
    intelligence = life_stats["intelligence"]
    reputation = life_stats["reputation"]
    alive = life_stats["alive"]

    last_event = await database.fetch_one(
        "SELECT id, scenario, possible_choices, decided_choice FROM events WHERE life_id = :life_id ORDER BY created_at DESC LIMIT 1",
        {"life_id": life_id}
    )
    event_id = last_event["id"]
    scenario = last_event["scenario"]
    possible_choices = last_event["possible_choices"]
    decided_choice = last_event["decided_choice"]


    return{
        "event_id": event_id,
        "age": age,
        "money": money,
        "happiness": happiness,
        "intelligence": intelligence,
        "reputation": reputation,
        "alive": alive,
        "scenario": scenario,
        "possible_choices": possible_choices,
        "decided_choice": decided_choice
    }
