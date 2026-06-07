create table users (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    credits integer default 30,
    stripe_customer_id text,
    created_at timestamptz not null default now()
);

alter table users enable row level security;

