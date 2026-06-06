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

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File, Form, Query
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

# ---------- Setup ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mergent")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = os.environ.get("APP_NAME", "mergent")
storage_key: Optional[str] = None


def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str):
    key = init_storage()
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


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
app = FastAPI(title="Mergent Agency API")
api = APIRouter(prefix="/api")


@api.get("/")
async def root():
    return {"service": "mergent", "status": "ok"}


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
    "agency_name": "mergent",
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
    try:
        data, content_type = get_object(path)
    except requests.HTTPError:
        raise HTTPException(status_code=404, detail="File not found")
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
    title: str = Form(...),
    market: str = Form(...),
    category: str = Form(...),
    live_url: str = Form(""),
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_admin),
):
    image_path = ""
    if file is not None:
        ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin").lower()
        path = f"{APP_NAME}/projects/{uuid.uuid4()}.{ext}"
        data = await file.read()
        result = put_object(path, data, file.content_type or "application/octet-stream")
        image_path = result["path"]
    doc = {
        "id": str(uuid.uuid4()),
        "title": title,
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
    title: Optional[str] = Form(None),
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
    if title is not None:
        update["title"] = title
    if market is not None:
        update["market"] = market
    if category is not None:
        update["category"] = category
    if live_url is not None:
        update["live_url"] = live_url
    if file is not None:
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
async def create_lead(payload: LeadIn):
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
    await db.leads.update_one({"id": lead_id}, {"$set": {"status": status}})
    return {"ok": True}


# ---------- Startup ----------
SEED_PROJECTS = [
    {"title": "متجر إلكتروني فاخر للأزياء", "market": "arab", "category": "stores", "live_url": "https://example.com/luxury-fashion", "image_path": ""},
    {"title": "منصة استشارات قانونية", "market": "arab", "category": "websites", "live_url": "https://example.com/legal", "image_path": ""},
    {"title": "متجر إلكترونيات متقدم", "market": "arab", "category": "stores", "live_url": "https://example.com/electronics", "image_path": ""},
    {"title": "موقع شركة عقارية", "market": "arab", "category": "websites", "live_url": "https://example.com/realestate", "image_path": ""},
    {"title": "Premium SaaS Dashboard", "market": "foreign", "category": "websites", "live_url": "https://example.com/saas", "image_path": ""},
    {"title": "International Cosmetics Store", "market": "foreign", "category": "stores", "live_url": "https://example.com/cosmetics", "image_path": ""},
    {"title": "Mobile Banking Identity", "market": "foreign", "category": "other", "live_url": "https://example.com/banking", "image_path": ""},
    {"title": "تطبيق توصيل طلبات", "market": "arab", "category": "other", "live_url": "https://example.com/delivery", "image_path": ""},
    {"title": "Crypto Trading Platform", "market": "foreign", "category": "websites", "live_url": "https://example.com/crypto", "image_path": ""},
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


async def seed_projects():
    count = await db.projects.count_documents({})
    if count > 0:
        return
    now = datetime.now(timezone.utc)
    docs = []
    for i, p in enumerate(SEED_PROJECTS):
        docs.append({
            "id": str(uuid.uuid4()),
            "title": p["title"],
            "market": p["market"],
            "category": p["category"],
            "live_url": p["live_url"],
            "image_path": "",
            "image_external_url": PORTFOLIO_IMAGES[i % len(PORTFOLIO_IMAGES)],
            "created_at": (now - timedelta(days=i)).isoformat(),
        })
    await db.projects.insert_many(docs)
    logger.info(f"Seeded {len(docs)} projects")


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
    try:
        init_storage()
        logger.info("Object storage ready")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")


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
