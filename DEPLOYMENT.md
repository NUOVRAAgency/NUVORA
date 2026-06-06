# NUVORA — Self-Hosting & Deployment Guide

This guide takes a freshly-cloned NUVORA repository and runs it on any standard
Linux server **with zero Emergent-only dependencies**. The app is just a
React frontend + FastAPI backend + MongoDB database, plus a folder of uploaded
images on disk.

---

## 1. Repository layout

```
NUVORA/
├── backend/                FastAPI app
│   ├── server.py
│   ├── requirements.txt
│   ├── .env.example         <- copy to .env and fill in
│   └── uploads/             <- created automatically; project & logo images live here
├── frontend/                React app (Create React App / CRACO)
│   ├── package.json
│   ├── .env.example         <- copy to .env and fill in
│   └── src/
└── DEPLOYMENT.md            (this file)
```

The codebase has been audited and stripped of any "Emergent-only" layer:

- ✅ **File storage**: local filesystem (`backend/uploads/`). No external object store.
- ✅ **Authentication**: custom JWT + bcrypt — already portable.
- ✅ **LLM/AI features**: none used at runtime.
- ✅ **Database**: standard MongoDB via `motor`.

---

## 2. Backend setup

### 2.1 Python dependencies (`backend/requirements.txt`)

```
fastapi==0.110.1
uvicorn==0.25.0
python-dotenv>=1.0.1
pydantic>=2.6.4
email-validator>=2.2.0
pyjwt>=2.10.1
bcrypt==4.1.3
motor==3.3.1
pymongo==4.5.0
python-multipart>=0.0.9
requests>=2.31.0
```

Install:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.2 Backend environment variables (`backend/.env`)

Copy the template and fill in your values:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | Description |
|---|---|---|
| `MONGO_URL` | ✅ | MongoDB connection string (e.g. `mongodb://localhost:27017` or Atlas URL). |
| `DB_NAME` | ✅ | Database name (e.g. `nuvora`). |
| `JWT_SECRET` | ✅ | Long random secret. Generate: `python -c "import secrets;print(secrets.token_hex(32))"`. |
| `ADMIN_EMAIL` | ✅ | Email used to seed the first admin on startup. |
| `ADMIN_PASSWORD` | ✅ | Password for that admin. Change immediately after first login. |
| `APP_NAME` | optional | Folder prefix used inside `UPLOAD_DIR` (default `nuvora`). |
| `UPLOAD_DIR` | optional | Absolute path where uploaded files are stored (default `./uploads`). |
| `CORS_ORIGINS` | optional | Comma-separated list of allowed origins or `*` (default `*`). |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | optional | Enable Telegram lead notifications. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `NOTIFY_EMAIL` | optional | Enable email lead notifications. |

### 2.3 Run the backend

Development:

```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Production (recommended: `gunicorn` with `uvicorn` workers, behind nginx):

```bash
pip install gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

On first boot the backend will:

1. Create the `uploads/` directory.
2. Seed the admin user from `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
3. Seed the default site settings.
4. Seed 9 sample bilingual portfolio projects (only if the projects collection is empty).

All API routes are prefixed with `/api`. Health-check: `GET /api/`.

---

## 3. Frontend setup

### 3.1 Node dependencies (`frontend/package.json`)

The existing `frontend/package.json` is already standard CRA + Tailwind + shadcn.
Install with **yarn** (recommended) or npm:

```bash
cd frontend
yarn install
# or:  npm install --legacy-peer-deps
```

### 3.2 Frontend environment variables (`frontend/.env`)

```bash
cp frontend/.env.example frontend/.env
```

| Variable | Required | Description |
|---|---|---|
| `REACT_APP_BACKEND_URL` | ✅ | Public origin where the backend is reachable. Local dev: `http://localhost:8001`. Production: `https://api.nuvora.com` (or whatever host serves `/api`). |
| `WDS_SOCKET_PORT` | optional | Only needed when developing behind an HTTPS proxy; safe to leave as `443`. |

> The frontend calls `${REACT_APP_BACKEND_URL}/api/...`. If your nginx routes
> `/api/*` to the FastAPI backend on the same hostname as the frontend, set
> `REACT_APP_BACKEND_URL` to that public hostname (without `/api`).

### 3.3 Run the frontend

Development:

```bash
yarn start
# CRA dev server on http://localhost:3000
```

Production build:

```bash
yarn build
# Static files in frontend/build/  — serve via nginx, Caddy, S3+CloudFront, Vercel, Netlify, etc.
```

---

## 4. MongoDB

Any MongoDB ≥ 4.4 works (local, Docker, Atlas, DigitalOcean managed, etc.).

Quick local instance with Docker:

```bash
docker run -d --name nuvora-mongo -p 27017:27017 -v nuvora-mongo:/data/db mongo:7
```

To migrate existing data from the current deployment:

```bash
# Dump from current host:
mongodump --uri="$OLD_MONGO_URL" --out=./nuvora-db-backup

# Restore on new host:
mongorestore --uri="$NEW_MONGO_URL" ./nuvora-db-backup
```

The database holds three collections: `users`, `projects`, `leads`, `settings`.
All documents are pure JSON-friendly (no Emergent-specific BSON types).

---

## 5. nginx reverse-proxy example (single domain)

`/etc/nginx/sites-available/nuvora`:

```nginx
server {
    listen 80;
    server_name nuvora.com www.nuvora.com;

    # frontend static build
    root /var/www/nuvora/frontend/build;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    # backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 25M;          # for image uploads
    }
}
```

Add HTTPS with Let's Encrypt:

```bash
sudo certbot --nginx -d nuvora.com -d www.nuvora.com
```

---

## 6. systemd service for the backend (optional but recommended)

`/etc/systemd/system/nuvora-backend.service`:

```ini
[Unit]
Description=NUVORA FastAPI backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/nuvora/backend
EnvironmentFile=/var/www/nuvora/backend/.env
ExecStart=/var/www/nuvora/backend/.venv/bin/gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8001
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nuvora-backend
```

---

## 7. First-run checklist

- [ ] MongoDB is reachable from the backend host (`mongo $MONGO_URL`).
- [ ] `backend/.env` filled in with strong `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.
- [ ] `frontend/.env` points `REACT_APP_BACKEND_URL` at your public API origin.
- [ ] `uploads/` directory is writable by the backend user.
- [ ] Visit the site, then `/admin/login` and sign in with your admin credentials.
- [ ] Change `ADMIN_PASSWORD` immediately (you can also rotate it via env + restart).
- [ ] Open the Admin → Settings tab and update phone, WhatsApp, email, agency logo.
- [ ] (Optional) Set `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` for instant lead alerts.

That's it — NUVORA now runs end-to-end on your own infrastructure with no
external service dependencies.
