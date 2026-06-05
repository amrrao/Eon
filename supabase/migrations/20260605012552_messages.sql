create table messages (
    id uuid primary key default gen_random_uuid(),
    relationship_id uuid not null references relationships(id),
    sent_by_whom text,
    message text,
    update_to_strength_number integer,
    update_to_happiness integer,
    update_to_relationship_type text,
    created_at timestamptz not null default now()
);

alter table messages enable row level security;