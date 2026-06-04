Data Model

Users
Id (primary key)
Email
Credits 
Password_hash
created_at

Lives
Id (primary key)
user_id (foreign key)
Money_stat
Intelligence_stat
Happiness_stat
Reputation_stat
Alive
Age 
unread_message_count
Rolling_summary
created_at

Events
Id (primary key)
life_id (foreign key)
Scenario
Decided_choice
Update_to_money
Update_to_intelligence
Update_to_happiness
update_to_reputation
Update_to_age
created_at

Relationships
Id (primary key)
life_id (foreign key)
Character_name
Strength_number
Relationship_type 
Unread_message_count
Rolling summary
Created_at 

Messages
Id (primary key)
relationship_id (foreign key)
Sentbywho
Message
Change_to_strength_number
Change_to_happiness
Change_to_relationship_type 
Created_at

API Design

POST auth/login
Info sent: email, password
Action: checks db to see if that user is there and password matches
returns: jwt

POST auth/signup
Info sent: email, password
Action: Enters user details into db, maybe sends confirm email?
Returns: jwt

POST /lives
Info sent: starting preferences (e.g. gender)
Action: Generates full starting life info with preferences included and adds to DB, generate event too
Returns: json randomly generated starting life info e.g. location, parents, etc to frontend, and event

POST lives/{life_id}/events
Info sent: lifeid(is this necessary bc ur already inside that life)
Action: puts rolling summary and stats into openai to get new scenario, puts choices and scenario into DB events row, updates unread message count
Returns: json with scenario description, possible choices, messages, unread message count

PATCH /lives/{life_id}/events/{event_id}
Info sent: decision between choices
Action: puts decision and rolling summary into openai, openai makes stat updates and new rolling summary, fills full db events row now
Returns: success

POST /lives/{life_id}/relationships/{relationship_id}/messages
Info sent: message, lifeid, relationship character receiver
Action: inserts message, sent by who in a row in db, updates rolling summary and message into openai, gets a response, also gets updates to happiness and relationship stats. creates new row for response as well
Returns: response, stat updates

GET /lives/{life_id}
Info sent: life id
Action: Loads that life to frontend home tab, including last event. Loads pending scenario if decided choice is null, Loads number of unread messages to put red dot if >0
Returns: scenario, unread messages

GET /lives/{life_id}/relationships
Info sent: life id
Action: gets relationships list eg. names , unread messages to bold name if unread
Returns: list of relationships (for message page), name, number of unread messages for each

GET /lives/{life_id}/relationships/{relationship_id}/messages
Info sent: life id, relationship id
Action: Loads messages, gets unread messages for that person, 
Returns: list of relationships (for imessage page)

PATCH /lives/{life_id}/relationships/{relationship_id}/messages
Info sent: life id, relationship
Action: sets unread_messages to that relationship to 0 and subtracts the old number from unread messages for that life id 
Returns: success 
