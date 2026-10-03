# Eon

AI life-simulation platform where every choice and interaction shapes an evolving character's story.

🔗 **Live:** [playeon.co](https://playeon.co/)

## What it does
Eon runs on two core systems: a game/scenario choice engine that drives the main storyline, and a texting system where you can message individual characters directly. Everything affects everything else: choices in the main story shape how characters text you, and conversations while texting carry back into the next story scenario. It's all one connected world, rather than a series of disconnected interactions.

## Architecture
- **Backend:** FastAPI + PostgreSQL (Supabase), with a dual-conversation LLM system for real-time life-simulation and per-character messaging, synced via a Postgres-backed buffer that avoids both the blocking, slow calls you'd get from waiting on each character update synchronously after a scenario generates, and the race condition simple async calls would still leave open
- **Payments:** Credit-gated system built on Stripe, with webhook-based idempotency handling to prevent duplicate credit grants on retries
- **Frontend:** Deployed on Vercel
- **Backend infra:** Deployed on AWS EC2 with CI/CD

## Setup

### Frontend
\`\`\`
cd frontend
cp .env.example .env.local
npm install
npm run dev
\`\`\`

### Backend
\`\`\`
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
\`\`\`

## Status
Currently polishing and iterating to improve scenario quality and engagement.