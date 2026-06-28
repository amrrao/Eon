create table events (
    id uuid primary key default gen_random_uuid(),
    life_id uuid not null references lives(id) on delete cascade,
    scenario text,
    possible_choices jsonb,
    decided_choice text,
    update_to_money integer,
    update_to_intelligence integer,
    update_to_happiness integer,
    update_to_reputation integer,
    update_to_age integer,
    created_at timestamptz not null default now()
);

alter table events enable row level security;