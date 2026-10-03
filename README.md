# Eon

AI life-simulation platform where every choice and interaction shapes an evolving character's world.

🔗 **Live:** [playeon.co](https://playeon.co/)

## What it does
Eon runs on two core systems: a game/scenario choice engine that drives the main storyline, and a texting system where you can message individual characters directly. Everything affects everything else: choices in the main story shape how characters text you, and conversations while texting carry back into the next story scenario. It's all one connected world, rather than a series of disconnected interactions.

## Architecture
- **Backend:** FastAPI + PostgreSQL (Supabase), with a dual-conversation LLM system for life-simulation and per-character messaging, synced via Postgres pending buffers (no per-character AI calls during scenario generation)
- **Payments:** Credit-gated system built on Stripe, with webhook-based idempotency handling to prevent duplicate credit grants on retries
- **Frontend:** Deployed on Vercel
- **Backend infra:** AWS EC2 running the API in Docker (`backend/Dockerfile`); GitHub Actions (`.github/workflows/deploy.yml`) SSHs into the instance on push to `main`, pulls latest, rebuilds the image, and restarts the container

## Setup

### Prerequisites
- Node.js
- Python 3.12+
- [Supabase CLI](https://supabase.com/docs/guides/cli) (for local DB + Auth), or a Supabase cloud project
- OpenAI API key
- Stripe keys (optional for local play if you only need auth + gameplay; required for buying credits)

### Supabase
From the repo root:

```bash
supabase start
supabase status
```

Use the local API URL, DB URL, and keys from `supabase status` in your env files. Apply migrations if needed (`supabase db reset` or your usual flow).

For a cloud project instead, create one in the Supabase dashboard, run the migrations in `supabase/migrations/`, and use those credentials.

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
cp .env.example .env
```

Fill `.env` (see `.env.example`):

- `DATABASE_URL`
- `SUPABASE_URL`, `SUPABASE_KEY` (prefer service role on the backend)
- `FRONTEND_URL` (e.g. `http://localhost:3000`)
- `OPENAI_API_KEY`
- Stripe vars if testing payments (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, price IDs)

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
cp .env.example .env.local
```

Fill `.env.local`:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (anon / publishable key)
- `NEXT_PUBLIC_API_URL` (e.g. `http://localhost:8000`)

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The API should already be running on port 8000.

## Status
Currently polishing and iterating to improve scenario quality and engagement.