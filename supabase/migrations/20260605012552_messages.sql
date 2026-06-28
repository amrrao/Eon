create table messages (
    id uuid primary key default gen_random_uuid(),
    relationship_id uuid not null references relationships(id) on delete cascade,
    sent_by_whom text,
    message text,
    created_at timestamptz not null default now()
);

alter table messages enable row level security;