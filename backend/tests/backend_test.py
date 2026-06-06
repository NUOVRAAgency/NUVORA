"""Backend API tests for Mergent agency."""
import os
import io
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Read from frontend .env if not in shell env
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                    break
    except Exception:
        pass
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
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
    for k in ("id", "title", "title_ar", "title_en", "description_ar", "description_en", "market", "category", "image_url", "created_at"):
        assert k in sample, f"missing field {k} in project"
    # Bilingual fields non-empty for seeded projects
    for p in items:
        assert p["title_ar"], f"title_ar empty for {p['id']}"
        assert p["title_en"], f"title_en empty for {p['id']}"
        assert p["description_ar"], f"description_ar empty for {p['id']}"
        assert p["description_en"], f"description_en empty for {p['id']}"
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
    assert s.get("agency_name") == "NUVORA", f"agency_name expected NUVORA, got {s.get('agency_name')}"
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
    r = requests.post(f"{API}/projects", data={"title_ar": "x", "title_en": "x", "market": "arab", "category": "websites"}, timeout=15)
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


# ---------- Lead status workflow (iteration 3) ----------
def _create_lead(session, suffix="status"):
    payload = {
        "name": f"TEST_{suffix}",
        "email": f"test_{suffix}@example.com",
        "phone": "+10000000000",
        "service": "websites",
        "message": "Status workflow test message.",
    }
    r = session.post(f"{API}/leads", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_create_lead_with_empty_notify_env_does_not_throw(session):
    """notify_lead must be best-effort when env vars empty — response still 200 + ok+id."""
    lid = _create_lead(session, "notify")
    assert lid
    # cleanup will happen via admin delete in next tests; do it now
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    tok = r.json()["access_token"]
    session.delete(f"{API}/leads/{lid}", headers={"Authorization": f"Bearer {tok}"}, timeout=15)


@pytest.mark.parametrize("status", ["contacted", "won", "lost", "new"])
def test_patch_lead_status_valid(session, auth_headers, status):
    lid = _create_lead(session, f"valid_{status}")
    try:
        r = session.patch(f"{API}/leads/{lid}", headers=auth_headers, data={"status": status}, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert body["status"] == status
        # verify persistence
        r2 = session.get(f"{API}/leads", headers=auth_headers, timeout=15)
        found = [l for l in r2.json() if l["id"] == lid]
        assert found and found[0]["status"] == status
    finally:
        session.delete(f"{API}/leads/{lid}", headers=auth_headers, timeout=15)


def test_patch_lead_status_invalid(session, auth_headers):
    lid = _create_lead(session, "invalid")
    try:
        r = session.patch(f"{API}/leads/{lid}", headers=auth_headers, data={"status": "garbage"}, timeout=15)
        assert r.status_code == 400, r.text
    finally:
        session.delete(f"{API}/leads/{lid}", headers=auth_headers, timeout=15)


def test_patch_lead_status_unauth(session, auth_headers):
    lid = _create_lead(session, "unauth")
    try:
        r = requests.patch(f"{API}/leads/{lid}", data={"status": "contacted"}, timeout=15)
        assert r.status_code == 401, f"expected 401 got {r.status_code}"
    finally:
        session.delete(f"{API}/leads/{lid}", headers=auth_headers, timeout=15)


def test_patch_lead_status_not_found(session, auth_headers):
    r = session.patch(f"{API}/leads/does-not-exist", headers=auth_headers, data={"status": "contacted"}, timeout=15)
    assert r.status_code == 404


# ---------- Project CRUD (admin) ----------
def test_project_crud_bilingual(session, auth_headers):
    # CREATE with all four bilingual fields
    files = {"file": ("test.png", io.BytesIO(b"\x89PNG\r\n\x1a\nFAKE"), "image/png")}
    data = {
        "title_ar": "TEST_مشروع",
        "title_en": "TEST_Project",
        "description_ar": "وصف عربي",
        "description_en": "English description",
        "market": "arab",
        "category": "websites",
        "live_url": "https://example.com/x",
    }
    r = session.post(f"{API}/projects", headers=auth_headers, data=data, files=files, timeout=60)
    assert r.status_code == 200, r.text
    proj = r.json()
    pid = proj["id"]
    assert proj["title_ar"] == "TEST_مشروع"
    assert proj["title_en"] == "TEST_Project"
    assert proj["description_ar"] == "وصف عربي"
    assert proj["description_en"] == "English description"
    assert proj["title"] == "TEST_مشروع"  # legacy compat
    assert proj["image_url"], "image_url should be set after upload"

    # UPDATE title_en independently
    r = session.put(f"{API}/projects/{pid}", headers=auth_headers, data={"title_en": "TEST_Project_Updated"}, timeout=30)
    assert r.status_code == 200
    updated = r.json()
    assert updated["title_en"] == "TEST_Project_Updated"
    assert updated["title_ar"] == "TEST_مشروع"  # unchanged

    # UPDATE description_en independently
    r = session.put(f"{API}/projects/{pid}", headers=auth_headers, data={"description_en": "Updated English desc"}, timeout=30)
    assert r.status_code == 200
    assert r.json()["description_en"] == "Updated English desc"

    # UPDATE description_ar independently
    r = session.put(f"{API}/projects/{pid}", headers=auth_headers, data={"description_ar": "وصف محدث"}, timeout=30)
    assert r.status_code == 200
    assert r.json()["description_ar"] == "وصف محدث"

    # UPDATE title_ar (should also sync legacy title)
    r = session.put(f"{API}/projects/{pid}", headers=auth_headers, data={"title_ar": "TEST_مشروع_محدث"}, timeout=30)
    assert r.status_code == 200
    assert r.json()["title_ar"] == "TEST_مشروع_محدث"
    assert r.json()["title"] == "TEST_مشروع_محدث"

    # VERIFY persisted via list (GET)
    r = session.get(f"{API}/projects", timeout=15)
    found = [p for p in r.json() if p["id"] == pid]
    assert found
    fp = found[0]
    assert fp["title_ar"] == "TEST_مشروع_محدث"
    assert fp["title_en"] == "TEST_Project_Updated"
    assert fp["description_ar"] == "وصف محدث"
    assert fp["description_en"] == "Updated English desc"

    # DELETE
    r = session.delete(f"{API}/projects/{pid}", headers=auth_headers, timeout=15)
    assert r.status_code == 200

    # Verify deleted
    r = session.get(f"{API}/projects", timeout=15)
    assert not any(p["id"] == pid for p in r.json())


def test_create_project_optional_description_defaults(session, auth_headers):
    # POST without description fields → should default to empty string
    data = {
        "title_ar": "TEST_NoDesc",
        "title_en": "TEST_NoDesc_EN",
        "market": "foreign",
        "category": "other",
    }
    r = session.post(f"{API}/projects", headers=auth_headers, data=data, timeout=30)
    assert r.status_code == 200, r.text
    proj = r.json()
    assert proj["description_ar"] == ""
    assert proj["description_en"] == ""
    # Cleanup
    session.delete(f"{API}/projects/{proj['id']}", headers=auth_headers, timeout=15)


def test_create_project_requires_titles(session, auth_headers):
    # Missing title_en → should 422
    r = session.post(f"{API}/projects", headers=auth_headers, data={"title_ar": "x", "market": "arab", "category": "websites"}, timeout=15)
    assert r.status_code == 422, f"expected 422, got {r.status_code}: {r.text}"
    # Missing title_ar → should 422
    r = session.post(f"{API}/projects", headers=auth_headers, data={"title_en": "x", "market": "arab", "category": "websites"}, timeout=15)
    assert r.status_code == 422


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
