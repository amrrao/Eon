CREATE TABLE processed_events (
    id uuid primary key default gen_random_uuid(),
    stripe_event_id text unique not null,
    created_at timestamptz not null default now()
);

ALTER TABLE processed_events ENABLE ROW LEVEL SECURITY;