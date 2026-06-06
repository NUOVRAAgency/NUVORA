"""Backend API tests for Mergent agency."""
import os
import io
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://digital-mergent.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@mergent.com"
ADMIN_PASSWORD = "Admin@123"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    return s


@pytest.fixture(scope="session")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed {r.status_code} {r.text}"
    data = r.json()
    assert data["role"] == "admin"
    assert data["access_token"]
    return data["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------- Health ----------
def test_root(session):
    r = session.get(f"{API}/", timeout=15)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


# ---------- Projects (public) ----------
def test_projects_seeded(session):
    r = session.get(f"{API}/projects", timeout=20)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert len(items) >= 9, f"Expected 9 seeded projects, got {len(items)}"
    sample = items[0]
    for k in ("id", "title", "market", "category", "image_url", "created_at"):
        assert k in sample
    # market and category constrained values
    markets = {p["market"] for p in items}
    cats = {p["category"] for p in items}
    assert markets.issubset({"arab", "foreign"})
    assert cats.issubset({"websites", "stores", "other"})


# ---------- Settings ----------
def test_settings_defaults(session):
    r = session.get(f"{API}/settings", timeout=15)
    assert r.status_code == 200
    s = r.json()
    assert s["phone"] == "+1 (608) 979-3938"
    assert s["email"] == "nuvoranuvora760@gmail.com"
    assert s.get("whatsapp")


# ---------- Auth ----------
def test_login_invalid(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"}, timeout=15)
    assert r.status_code == 401


def test_auth_me(session, auth_headers):
    r = session.get(f"{API}/auth/me", headers=auth_headers, timeout=15)
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == ADMIN_EMAIL
    assert me["role"] == "admin"


def test_projects_write_requires_auth():
    r = requests.post(f"{API}/projects", data={"title": "x", "market": "arab", "category": "websites"}, timeout=15)
    assert r.status_code == 401


# ---------- Leads ----------
def test_create_lead_public(session):
    payload = {
        "name": "TEST_Tester",
        "email": "test_tester@example.com",
        "phone": "+10000000000",
        "service": "websites",
        "message": "Hello, this is a test message.",
    }
    r = session.post(f"{API}/leads", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is True
    assert "id" in data
    pytest.lead_id = data["id"]


def test_list_leads_admin(session, auth_headers):
    r = session.get(f"{API}/leads", headers=auth_headers, timeout=15)
    assert r.status_code == 200
    leads = r.json()
    assert any(l["id"] == pytest.lead_id for l in leads)


def test_leads_requires_auth():
    r = requests.get(f"{API}/leads", timeout=10)
    assert r.status_code == 401


def test_delete_lead(session, auth_headers):
    r = session.delete(f"{API}/leads/{pytest.lead_id}", headers=auth_headers, timeout=15)
    assert r.status_code == 200
    # verify gone
    r2 = session.get(f"{API}/leads", headers=auth_headers, timeout=15)
    assert not any(l["id"] == pytest.lead_id for l in r2.json())


# ---------- Project CRUD (admin) ----------
def test_project_crud(session, auth_headers):
    # CREATE
    files = {"file": ("test.png", io.BytesIO(b"\x89PNG\r\n\x1a\nFAKE"), "image/png")}
    data = {"title": "TEST_Project", "market": "arab", "category": "websites", "live_url": "https://example.com/x"}
    r = session.post(f"{API}/projects", headers=auth_headers, data=data, files=files, timeout=60)
    assert r.status_code == 200, r.text
    proj = r.json()
    pid = proj["id"]
    assert proj["title"] == "TEST_Project"
    assert proj["image_url"], "image_url should be set after upload"

    # UPDATE
    r = session.put(f"{API}/projects/{pid}", headers=auth_headers, data={"title": "TEST_Project_Updated"}, timeout=30)
    assert r.status_code == 200
    assert r.json()["title"] == "TEST_Project_Updated"

    # VERIFY persisted via list
    r = session.get(f"{API}/projects", timeout=15)
    found = [p for p in r.json() if p["id"] == pid]
    assert found and found[0]["title"] == "TEST_Project_Updated"

    # DELETE
    r = session.delete(f"{API}/projects/{pid}", headers=auth_headers, timeout=15)
    assert r.status_code == 200

    # Verify deleted
    r = session.get(f"{API}/projects", timeout=15)
    assert not any(p["id"] == pid for p in r.json())


# ---------- Settings update + logo ----------
def test_settings_update(session, auth_headers):
    # get current first
    cur = session.get(f"{API}/settings", timeout=10).json()
    new_phone = "+1 (608) 979-3938"  # same value to avoid disturbing UI tests
    r = session.put(f"{API}/settings", headers={**auth_headers, "Content-Type": "application/json"},
                    json={"phone": new_phone, "agency_name": cur.get("agency_name", "mergent")}, timeout=15)
    assert r.status_code == 200
    assert r.json()["phone"] == new_phone


def test_logo_upload(session, auth_headers):
    files = {"file": ("logo.png", io.BytesIO(b"\x89PNG\r\n\x1a\nFAKE"), "image/png")}
    r = session.post(f"{API}/settings/logo", headers=auth_headers, files=files, timeout=60)
    assert r.status_code == 200, r.text
    assert r.json().get("logo_path")
