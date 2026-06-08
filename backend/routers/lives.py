from fastapi import APIRouter, Depends, HTTPException
from dependancies import get_current_user
from database import database
from pydantic import BaseModel
from openai import AsyncOpenAI
import json
import uuid

client = AsyncOpenAI()
router = APIRouter()

class CreateLifeRequest(BaseModel):
    gender: str


class Decision(BaseModel):
    decision: str


@router.post("/")
async def create_life(body: CreateLifeRequest, user = Depends(get_current_user)):
    credits = await database.fetch_one(
        "Select credits from users where id = :id",
        {"id": user.id}
        )
    if credits["credits"]<1:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a life simulator game engine."},
            {"role": "user", "content": f"Generate a starting life scenario for a {body.gender} baby just born in second person. Return JSON only with fields: scenario (string), choices (array of 3 strings), mother_name (string), father_name (string)"}
        ],
        response_format={"type": "json_object"}
    )
    response = completion.choices[0].message.content
    life_data = json.loads(response)
    print("LIFE DATA:", life_data)
    mom_name = life_data["mother_name"]
    dad_name = life_data["father_name"]
    scenario = life_data["scenario"]
    choices = life_data["choices"]
    life_id = str(uuid.uuid4())
    await database.execute(
        "Insert into lives (id, user_id, gender, unread_message_count) values (:id, :user_id, :gender, :unread_message_count)",
        {"id": life_id,
        "user_id": str(user.id), 
        "gender": body.gender,
        "unread_message_count": 0}
    )
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
    await database.execute(
        "Insert into relationships (id, life_id, character_name, strength_number, relationship_type, unread_message_count) values (:id, :life_id, :character_name, :strength_number, :relationship_type, :unread_message_count)",
        {"id": relationship_id_dad,
        "life_id": life_id, 
        "character_name": dad_name,
        "strength_number": 80,
        "relationship_type": "father",
        "unread_message_count": 0}
    )
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

@router.post("/{life_id}/events")
async def generate_event(life_id: str, user = Depends(get_current_user)):
    credits = await database.fetch_one(
        "Select credits from users where id = :id",
        {"id": user.id}
        )

    if credits["credits"]<1:
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
    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a life simulator game engine."},
            {"role": "user", "content": f"Generate a starting life scenario for this life: {rolling_summary} age {age} with these stats: money {money}, happiness {happiness}/100, intelligence {intelligence}/100, reputation {reputation}/100. Return JSON only with fields: scenario (string), choices (array of 3 strings), and only if you are adding a relationship, name_of_person (string), relationship_type (string), relationship_strength (int), and message_from_relationship (string)"}
        ],
        response_format={"type": "json_object"}
    )
    response = completion.choices[0].message.content
    life_data = json.loads(response)
    print("LIFE DATA:", life_data)
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

    relationship_id = str(uuid.uuid4())
    relationship_name = life_data.get("relationship_name")
    relationship_type = life_data.get("relationship_type")
    relationship_strength = life_data.get("relationship_strength")

    message_id = str(uuid.uuid4())
    message_from_relationship = life_data.get("message_from_relationship")

    if relationship_name != None:

        await database.execute(
            "Insert into relationships (id, life_id, character_name, strength_number, relationship_type, unread_message_count) values (:id, :life_id, :character_name, :strength_number, :relationship_type, :unread_message_count)",
            {"id": relationship_id,
            "life_id": life_id, 
            "character_name": relationship_name,
            "strength_number": relationship_strength,
            "relationship_type": relationship_type,
            "unread_message_count": 1}
        )
        await database.execute(
            "UPDATE lives SET unread_message_count = unread_message_count + 1 WHERE id = :id",
            {"id": life_id}
        )

        await database.execute(
            "Insert into messages (id, relationship_id, sent_by_whom, message) values (:id, :relationship_id, :sent_by_whom, :message)",
            {"id": message_id,
            "relationship_id": relationship_id, 
            "sent_by_whom": relationship_name,
            "message": message_from_relationship}
        )

    await database.execute(
        "UPDATE users set credits = credits -1 where id = :id",
        {"id": str(user.id)}
    )

    return{
        "event_id": event_id,
        "scenario": scenario,
        "choices": choices,
        "relationship_name": relationship_name,
        "relationship_type": relationship_type,
        "message_from_relationship": message_from_relationship,
    }



@router.patch("/{life_id}/events/{event_id}")
async def update_choice(body: Decision, life_id: str, event_id: str, user = Depends(get_current_user)):
   

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
            {"role": "system", "content": "You are a life simulator game engine."},
            {"role": "user", "content": f"A user of age {age} and with a life rolling summary: {rolling_summary} and stats: {money}$, happiness {happiness}/100, intelligence {intelligence}/100, reputation {reputation}/100 just made the choice to {body.decision} when asked {scenario}. In a json give the updated_rolling_summary (string), the deltas update_to_money (integer), update_to_intelligence (integer), update_to_happiness (integer), update_to_reputation (integer), update_to_age (integer) if you think any updates are necessary."}
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
        "UPDATE lives SET money = money + :update_to_money, intelligence = intelligence + :update_to_intelligence, happiness = happiness + :update_to_happiness, reputation = reputation + :update_to_reputation, age = age + :update_to_age, rolling_summary = :rolling_summary WHERE id = :life_id",
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

    return {"status": "success"}