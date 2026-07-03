create table relationships(
    id uuid primary key default gen_random_uuid(),
    life_id uuid not null references lives(id) on delete cascade,
    character_name text,
    strength_number integer,
    relationship_type text,
    unread_message_count integer,
    openai_conversation_id text,
    pending_world_update text,
    created_at timestamptz not null default now()
);

alter table relationships enable row level security;