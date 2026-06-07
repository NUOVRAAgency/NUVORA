from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import uuid
import logging
import bcrypt
import jwt
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File, Form, Query, BackgroundTasks
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

# ---------- Setup ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("nuvora")

# تم التعديل هنا لتجنب Crash إذا لم توجد المتغيرات
mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017/nuvora_db")
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get("DB_NAME", "nuvora_db")]

JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key-change-me")
JWT_ALG = "HS256"

APP_NAME = os.environ.get("APP_NAME", "nuvora")

# ---------- Local file storage ----------
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR") or (ROOT_DIR / "uploads")).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def _safe_storage_path(relative: str) -> Path:
    target = (UPLOAD_DIR / relative).resolve()
    if not str(target).startswith(str(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid path")
    return target

def put_object(path: str, data: bytes, content_type: str = "application/octet-stream") -> dict:
    target = _safe_storage_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {"path": path}

def get_object(path: str):
    target = _safe_storage_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    import mimetypes
    ctype, _ = mimetypes.guess_type(str(target))
    return target.read_bytes(), ctype or "application/octet-stream"

def notify_lead(lead: dict) -> None:
    text = (
        f"📩 New NUVORA Consultation Lead\n"
        f"Name: {lead.get('name')}\n"
        f"Email: {lead.get('email')}\n"
        f"Phone: {lead.get('phone') or '-'}\n"
        f"Service: {lead.get('service')}\n"
        f"Message: {lead.get('message')}"
    )
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if tg_token and tg_chat:
        try:
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_chat, "text": text, "disable_web_page_preview": True},
                timeout=10,
            )
        except Exception as e:
            logger.warning(f"Telegram notify failed: {e}")
    smtp_host = os.environ.get("SMTP_HOST", "")
    notify_to = os.environ.get("NOTIFY_EMAIL", "")
    if smtp_host and notify_to:
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(text, "plain", "utf-8")
            msg["Subject"] = f"NUVORA: New lead from {lead.get('name')}"
            msg["From"] = os.environ.get("SMTP_USER") or notify_to
            msg["To"] = notify_to
            with smtplib.SMTP(smtp_host, int(os.environ.get("SMTP_PORT", "587"))) as s:
                s.starttls()
                if os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASS"):
                    s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
                s.send_message(msg)
        except Exception as e:
            logger.warning(f"SMTP notify failed: {e}")

# ---------- Helpers & Models ----------
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

async def get_current_admin(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user = await db.users.find_one({"id": payload["sub"]})
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=401, detail="Not authorized")
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class LeadIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: Optional[str] = ""
    service: str
    message: str = Field(min_length=2, max_length=4000)

# ---------- App ----------
app = FastAPI(title="NUVORA Agency API")
api = APIRouter(prefix="/api")

@api.get("/")
async def root():
    return {"service": "nuvora", "status": "ok"}

# [باقي الكود كما هو تماماً..]
app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown():
    client.close()

