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

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"

APP_NAME = os.environ.get("APP_NAME", "nuvora")

# ---------- Local file storage (portable, no external dependencies) ----------
# Files are stored under UPLOAD_DIR (default: backend/uploads) and served via /api/files/{path}.
# Override the storage location with the UPLOAD_DIR environment variable when self-hosting
# (e.g. UPLOAD_DIR=/var/lib/nuvora/uploads).
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR") or (ROOT_DIR / "uploads")).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _safe_storage_path(relative: str) -> Path:
    """Resolve a relative storage path under UPLOAD_DIR and prevent path traversal."""
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
    """Best-effort outbound notification (Telegram + SMTP). Never raises."""
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



def init_storage():
    """Kept for backwards-compatible startup logs. Local filesystem requires no init."""
    return str(UPLOAD_DIR)


def _legacy_remove_init():
    return None


# ---------- Helpers ----------
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
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]})
        if not user or user.get("role") != "admin":
            raise HTTPException(status_code=401, detail="Not authorized")
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------- Models ----------
class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ProjectIn(BaseModel):
    title: str
    market: str  # "arab" | "foreign"
    category: str  # "websites" | "stores" | "other"
    live_url: Optional[str] = ""
    image_path: Optional[str] = ""


class ProjectOut(ProjectIn):
    id: str
    image_url: Optional[str] = ""
    created_at: str


class SettingsIn(BaseModel):
    agency_name: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    support_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_path: Optional[str] = None


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


# ---------- Auth ----------
@api.post("/auth/login")
async def login(payload: LoginIn, response: Response):
    email = payload.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
    token = create_access_token(user["id"], email)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=43200,
        path="/",
    )
    return {"id": user["id"], "email": user["email"], "role": user["role"], "access_token": token}


@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_admin)):
    return user


# ---------- Settings ----------
DEFAULT_SETTINGS = {
    "id": "site",
    "agency_name": "NUVORA",
    "phone": "+1 (608) 979-3938",
    "whatsapp": "+16089793938",
    "support_phone": "+1 (608) 979-3938",
    "email": "nuvoranuvora760@gmail.com",
    "logo_path": "",
}


@api.get("/settings")
async def get_settings():
    doc = await db.settings.find_one({"id": "site"}, {"_id": 0})
    if not doc:
        doc = DEFAULT_SETTINGS
        await db.settings.insert_one(doc.copy())
    return doc


@api.put("/settings")
async def update_settings(payload: SettingsIn, user: dict = Depends(get_current_admin)):
    update_doc = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_doc:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db.settings.update_one({"id": "site"}, {"$set": update_doc}, upsert=True)
    doc = await db.settings.find_one({"id": "site"}, {"_id": 0})
    return doc


@api.post("/settings/logo")
async def upload_logo(file: UploadFile = File(...), user: dict = Depends(get_current_admin)):
    ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin").lower()
    path = f"{APP_NAME}/logo/{uuid.uuid4()}.{ext}"
    data = await file.read()
    result = put_object(path, data, file.content_type or "application/octet-stream")
    await db.settings.update_one({"id": "site"}, {"$set": {"logo_path": result["path"]}}, upsert=True)
    return {"logo_path": result["path"]}


# ---------- Files ----------
@api.get("/files/{path:path}")
async def serve_file(path: str):
    data, content_type = get_object(path)
    return Response(content=data, media_type=content_type)


# ---------- Projects ----------
def project_doc_to_out(doc: dict) -> dict:
    doc = {k: v for k, v in doc.items() if k != "_id"}
    if doc.get("image_path"):
        doc["image_url"] = f"/api/files/{doc['image_path']}"
    else:
        doc["image_url"] = ""
    return doc


@api.get("/projects")
async def list_projects():
    items = await db.projects.find({}).sort("created_at", -1).to_list(1000)
    return [project_doc_to_out(d) for d in items]


@api.post("/projects")
async def create_project(
    title_ar: str = Form(...),
    title_en: str = Form(...),
    description_ar: str = Form(""),
    description_en: str = Form(""),
    market: str = Form(...),
    category: str = Form(...),
    live_url: str = Form(""),
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_admin),
):
    image_path = ""
    if file is not None and file.filename:
        ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin").lower()
        path = f"{APP_NAME}/projects/{uuid.uuid4()}.{ext}"
        data = await file.read()
        result = put_object(path, data, file.content_type or "application/octet-stream")
        image_path = result["path"]
    doc = {
        "id": str(uuid.uuid4()),
        "title_ar": title_ar,
        "title_en": title_en,
        "description_ar": description_ar or "",
        "description_en": description_en or "",
        "title": title_ar,  # legacy compat
        "market": market,
        "category": category,
        "live_url": live_url or "",
        "image_path": image_path,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.projects.insert_one(doc.copy())
    return project_doc_to_out(doc)


@api.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    title_ar: Optional[str] = Form(None),
    title_en: Optional[str] = Form(None),
    description_ar: Optional[str] = Form(None),
    description_en: Optional[str] = Form(None),
    market: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    live_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_admin),
):
    existing = await db.projects.find_one({"id": project_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    update = {}
    if title_ar is not None:
        update["title_ar"] = title_ar
        update["title"] = title_ar
    if title_en is not None:
        update["title_en"] = title_en
    if description_ar is not None:
        update["description_ar"] = description_ar
    if description_en is not None:
        update["description_en"] = description_en
    if market is not None:
        update["market"] = market
    if category is not None:
        update["category"] = category
    if live_url is not None:
        update["live_url"] = live_url
    if file is not None and file.filename:
        ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin").lower()
        path = f"{APP_NAME}/projects/{uuid.uuid4()}.{ext}"
        data = await file.read()
        result = put_object(path, data, file.content_type or "application/octet-stream")
        update["image_path"] = result["path"]
    if update:
        await db.projects.update_one({"id": project_id}, {"$set": update})
    doc = await db.projects.find_one({"id": project_id})
    return project_doc_to_out(doc)


@api.delete("/projects/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(get_current_admin)):
    res = await db.projects.delete_one({"id": project_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True}


# ---------- Leads ----------
@api.post("/leads")
async def create_lead(payload: LeadIn, background: BackgroundTasks):
    doc = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone or "",
        "service": payload.service,
        "message": payload.message,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.leads.insert_one(doc.copy())
    # Best-effort outbound notification offloaded to a background task so the
    # client response stays fast even when Telegram/SMTP keys are configured.
    background.add_task(notify_lead, doc)
    return {"ok": True, "id": doc["id"]}


@api.get("/leads")
async def list_leads(user: dict = Depends(get_current_admin)):
    items = await db.leads.find({}, {"_id": 0}).sort("created_at", -1).to_list(2000)
    return items


@api.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, user: dict = Depends(get_current_admin)):
    res = await db.leads.delete_one({"id": lead_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"ok": True}


@api.patch("/leads/{lead_id}")
async def update_lead_status(lead_id: str, status: str = Form(...), user: dict = Depends(get_current_admin)):
    if status not in ("new", "contacted", "won", "lost"):
        raise HTTPException(status_code=400, detail="Invalid status")
    res = await db.leads.update_one({"id": lead_id}, {"$set": {"status": status}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"ok": True, "status": status}


# ---------- Startup ----------
SEED_PROJECTS = [
    {"title_ar": "متجر إلكتروني فاخر للأزياء", "title_en": "Luxury Fashion E-commerce", "description_ar": "متجر إلكتروني فاخر مع تجربة شراء سلسة لعلامة أزياء راقية.", "description_en": "Premium online store with a seamless shopping experience for a high-end fashion brand.", "market": "arab", "category": "stores", "live_url": "https://example.com/luxury-fashion"},
    {"title_ar": "منصة استشارات قانونية", "title_en": "Legal Consultation Platform", "description_ar": "منصة احترافية لحجز الاستشارات القانونية وإدارة العملاء.", "description_en": "Professional platform for booking legal consultations and managing clients.", "market": "arab", "category": "websites", "live_url": "https://example.com/legal"},
    {"title_ar": "متجر إلكترونيات متقدم", "title_en": "Advanced Electronics Store", "description_ar": "متجر إلكترونيات بتجربة بحث ذكية وخيارات دفع متعددة.", "description_en": "Electronics store with smart search and multiple payment options.", "market": "arab", "category": "stores", "live_url": "https://example.com/electronics"},
    {"title_ar": "موقع شركة عقارية", "title_en": "Real Estate Corporate Website", "description_ar": "موقع شركة عقارية مع قوائم تفاعلية وخريطة مشاريع.", "description_en": "Real estate corporate website with interactive listings and a project map.", "market": "arab", "category": "websites", "live_url": "https://example.com/realestate"},
    {"title_ar": "لوحة تحكم SaaS متميزة", "title_en": "Premium SaaS Dashboard", "description_ar": "لوحة تحكم برمجية متقدمة مع تحليلات في الوقت الفعلي.", "description_en": "Advanced product dashboard with real-time analytics.", "market": "foreign", "category": "websites", "live_url": "https://example.com/saas"},
    {"title_ar": "متجر مستحضرات تجميل عالمي", "title_en": "International Cosmetics Store", "description_ar": "تجربة تسوق راقية لعلامة تجميل عالمية متعددة العملات.", "description_en": "Elevated shopping experience for a global cosmetics brand with multi-currency support.", "market": "foreign", "category": "stores", "live_url": "https://example.com/cosmetics"},
    {"title_ar": "هوية تطبيق مصرفي", "title_en": "Mobile Banking Identity", "description_ar": "هوية بصرية وتجربة تطبيق مصرفي حديث.", "description_en": "Brand identity and mobile experience for a modern banking app.", "market": "foreign", "category": "other", "live_url": "https://example.com/banking"},
    {"title_ar": "تطبيق توصيل طلبات", "title_en": "Food Delivery App", "description_ar": "تطبيق توصيل مع تتبع مباشر وتجربة سلسة للمستخدم.", "description_en": "Delivery app with live order tracking and a smooth user experience.", "market": "arab", "category": "other", "live_url": "https://example.com/delivery"},
    {"title_ar": "منصة تداول العملات الرقمية", "title_en": "Crypto Trading Platform", "description_ar": "منصة تداول متطورة مع مخططات احترافية وأمان مصرفي.", "description_en": "Sophisticated trading platform with pro charts and bank-grade security.", "market": "foreign", "category": "websites", "live_url": "https://example.com/crypto"},
]

PORTFOLIO_IMAGES = [
    "https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?w=1200&q=80",
    "https://images.unsplash.com/photo-1551434678-e076c223a692?w=1200&q=80",
    "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1200&q=80",
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&q=80",
    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&q=80",
    "https://images.unsplash.com/photo-1522335789203-aaa2b09f6e72?w=1200&q=80",
    "https://images.unsplash.com/photo-1512486130939-2c4f79935e4f?w=1200&q=80",
    "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=1200&q=80",
    "https://images.unsplash.com/photo-1518186285589-2f7649de83e0?w=1200&q=80",
]


async def seed_admin():
    admin_email = os.environ["ADMIN_EMAIL"].lower()
    admin_password = os.environ["ADMIN_PASSWORD"]
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Seeded admin user: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )
        logger.info("Updated admin password from env")


async def seed_settings():
    existing = await db.settings.find_one({"id": "site"})
    if not existing:
        await db.settings.insert_one(DEFAULT_SETTINGS.copy())
        logger.info("Seeded default settings")
    elif existing.get("agency_name") in (None, "", "mergent"):
        await db.settings.update_one({"id": "site"}, {"$set": {"agency_name": "NUVORA"}})
        logger.info("Migrated agency_name to NUVORA")


async def seed_projects():
    # Remove legacy demo seeds (those with image_external_url) so we can re-seed with bilingual data
    legacy = await db.projects.count_documents({"image_external_url": {"$exists": True}, "title_ar": {"$exists": False}})
    if legacy > 0:
        await db.projects.delete_many({"image_external_url": {"$exists": True}, "title_ar": {"$exists": False}})
        logger.info(f"Removed {legacy} legacy seed projects (no bilingual fields)")
    # Backfill bilingual fields on any project missing them
    async for doc in db.projects.find({"$or": [{"title_ar": {"$exists": False}}, {"title_en": {"$exists": False}}]}):
        base_title = doc.get("title") or doc.get("title_ar") or "Project"
        await db.projects.update_one(
            {"id": doc["id"]},
            {"$set": {
                "title_ar": doc.get("title_ar") or base_title,
                "title_en": doc.get("title_en") or base_title,
                "description_ar": doc.get("description_ar") or "",
                "description_en": doc.get("description_en") or "",
            }},
        )
    count = await db.projects.count_documents({})
    if count > 0:
        return
    now = datetime.now(timezone.utc)
    docs = []
    for i, p in enumerate(SEED_PROJECTS):
        docs.append({
            "id": str(uuid.uuid4()),
            "title_ar": p["title_ar"],
            "title_en": p["title_en"],
            "title": p["title_ar"],
            "description_ar": p["description_ar"],
            "description_en": p["description_en"],
            "market": p["market"],
            "category": p["category"],
            "live_url": p["live_url"],
            "image_path": "",
            "image_external_url": PORTFOLIO_IMAGES[i % len(PORTFOLIO_IMAGES)],
            "created_at": (now - timedelta(days=i)).isoformat(),
        })
    await db.projects.insert_many(docs)
    logger.info(f"Seeded {len(docs)} bilingual projects")


@app.on_event("startup")
async def on_startup():
    try:
        await db.users.create_index("email", unique=True)
        await db.projects.create_index("created_at")
        await db.leads.create_index("created_at")
    except Exception as e:
        logger.warning(f"Index init: {e}")
    await seed_admin()
    await seed_settings()
    await seed_projects()
    logger.info(f"Local upload directory ready: {UPLOAD_DIR}")


# Override project serialization to also use external URL if available
def project_doc_to_out(doc: dict) -> dict:  # noqa: F811
    doc = {k: v for k, v in doc.items() if k != "_id"}
    if doc.get("image_path"):
        doc["image_url"] = f"/api/files/{doc['image_path']}"
    elif doc.get("image_external_url"):
        doc["image_url"] = doc["image_external_url"]
    else:
        doc["image_url"] = ""
    return doc


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown():
    client.close()
