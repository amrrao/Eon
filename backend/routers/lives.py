from fastapi import APIRouter, Depends, HTTPException
from dependancies import get_current_user
from database import database
from pydantic import BaseModel
import json
import uuid
from relationship_ai import init_relationship_conversation
from life_ai import init_life_conversation, call_life_response

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
        "Select character_texting_updates, age, money, happiness, intelligence, reputation from lives where id = :id",
        {"id": life_id}
        )
    character_texting_updates = life_stats["character_texting_updates"]
    age = life_stats["age"]
    money = life_stats["money"]
    happiness = life_stats["happiness"]
    intelligence = life_stats["intelligence"]
    reputation = life_stats["reputation"]

    existing_relationships = await database.fetch_all(
        "SELECT id, character_name, relationship_type FROM relationships WHERE life_id = :life_id",
        {"life_id": life_id}
    )
    existing_names = [f"{r['character_name']} ({r['relationship_type']})" for r in existing_relationships]

    life_data = await call_life_response(
        life_id,
        (
            "Generate the next scenario. Return JSON with fields: scenario (string), "
            "choices (array of 3 strings), new_relationships (array), and "
            "character_world_updates (array). Scenario should be under 50 words. "
            "Choices should be genuinely different. new_relationships must be [] unless "
            "a named person not in existing relationships becomes important. Each new relationship "
            "object should include name_of_person, relationship_type, relationship_strength, "
            "and message_from_relationship. character_world_updates should be [] unless existing "
            "characters need to know this scenario happened; each object should include "
            "character_name and update."
        ),
        age,
        money,
        happiness,
        intelligence,
        reputation,
        existing_names,
        character_texting_updates,
    )
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

    await database.execute(
        "UPDATE lives SET character_texting_updates = '' WHERE id = :id",
        {"id": life_id}
    )

    new_relationships = life_data.get("new_relationships", [])

    existing_character_names = {r["character_name"].lower() for r in existing_relationships}
    relationship_ids_by_name = {r["character_name"].lower(): r["id"] for r in existing_relationships}

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
        relationship_ids_by_name[name.lower()] = rel_id

    world_updates = life_data.get("character_world_updates", [])
    for item in world_updates:
        name = item.get("character_name")
        update = item.get("update")
        if not name or not update:
            continue
        rel_id = relationship_ids_by_name.get(name.lower())
        if not rel_id:
            continue
        await database.execute(
            "UPDATE relationships SET pending_world_update = COALESCE(pending_world_update || '\n', '') || :update WHERE id = :id",
            {"id": rel_id, "update": update}
        )

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
       "Select age, money, happiness, intelligence, reputation from lives where id = :id",
        {"id": life_id}
        )
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

    existing_relationships = await database.fetch_all(
        "SELECT id, character_name, relationship_type FROM relationships WHERE life_id = :life_id",
        {"life_id": life_id}
    )
    existing_names = [f"{r['character_name']} ({r['relationship_type']})" for r in existing_relationships]
    relationship_ids_by_name = {r["character_name"].lower(): r["id"] for r in existing_relationships}

    updates = await call_life_response(
        life_id,
        (
            f"The player chose: {body.decision}. The scenario was: {scenario}. "
            "Apply the consequences. Return JSON with fields: update_to_money (integer), "
            "update_to_intelligence (integer), update_to_happiness (integer), "
            "update_to_reputation (integer), update_to_age (integer), and "
            "character_world_updates (array). If a stat is not affected, set it to 0. "
            "Default to update_to_age 1 or more unless the choice creates a cliffhanger. "
            "character_world_updates should be [] unless existing characters need to know "
            "what happened; each object should include character_name and update."
        ),
        age,
        money,
        happiness,
        intelligence,
        reputation,
        existing_names,
    )
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
            age = age + :update_to_age
        WHERE id = :life_id""",
        {
            "update_to_money": update_to_money,
            "update_to_intelligence": update_to_intelligence,
            "update_to_happiness": update_to_happiness,
            "update_to_reputation": update_to_reputation,
            "update_to_age": update_to_age,
            "life_id": life_id
        }
    )

    world_updates = updates.get("character_world_updates", [])
    for item in world_updates:
        name = item.get("character_name")
        update = item.get("update")
        if not name or not update:
            continue
        rel_id = relationship_ids_by_name.get(name.lower())
        if not rel_id:
            continue
        await database.execute(
            "UPDATE relationships SET pending_world_update = COALESCE(pending_world_update || '\n', '') || :update WHERE id = :id",
            {"id": rel_id, "update": update}
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
