create table lives (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id),
    money integer default 0,
    intelligence integer default 5,
    happiness integer default 50,
    reputation integer default 50,
    age integer default 0,
    gender text,
    alive boolean default true,
    unread_message_count integer default 0, 
    rolling_summary text,
    created_at timestamptz not null default now()
);

alter table lives enable row level security;