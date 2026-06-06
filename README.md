# NUVORA — Digital Agency Platform

A premium bilingual (Arabic/English) digital-agency website + admin dashboard.
Standard stack, **fully portable**, no vendor lock-in:

- **Frontend**: React (CRA) + Tailwind + shadcn/ui + framer-motion
- **Backend**: FastAPI + Motor (async MongoDB) + JWT auth (bcrypt)
- **Database**: MongoDB
- **File storage**: local filesystem (`backend/uploads/`)

## Features

- Arabic-first RTL site with automatic browser-language detection and a manual AR/EN toggle
- Animated deep-teal hero with floating particle network
- Portfolio grid with double-tier filters (market × category) and bilingual project content
- Consultation intake form posting leads to the backend
- Minimalist contact icon-bar + click-to-call / click-to-mail / click-to-WhatsApp
- Floating WhatsApp button matching the brand palette
- Full Admin dashboard (`/admin`): CRUD for bilingual projects, dynamic site settings (phone, WhatsApp, email, logo), and a leads inbox with status workflow (new → contacted → won/lost)
- Optional outbound lead notifications via Telegram and/or SMTP email

## Quickstart

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # edit with MongoDB URL, JWT secret, admin creds
uvicorn server:app --reload --port 8001

# 2. Frontend
cd ../frontend
yarn install
cp .env.example .env        # set REACT_APP_BACKEND_URL=http://localhost:8001
yarn start
```

Visit:

- Public site: `http://localhost:3000/`
- Admin login: `http://localhost:3000/admin/login`

## Deployment

See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for a complete self-hosting guide (nginx config, systemd unit, MongoDB migration, environment variables).
