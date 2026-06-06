# Mergent Digital Agency — PRD

## Original Problem Statement (Summary)
Build a premium, production-ready full-stack web app for a digital agency named "mergent" with:
- Arabic RTL default UI, palette extracted from reference screenshots (light steel-blue header, deep teal hero, pure white portfolio sections).
- Header with logo, 3D language switcher (AR/EN), hamburger drawer.
- Hero: animated particle network, AI pill badge, headline "صناع تغيير", two stacked 3D CTAs (Solid white + transparent outlined), floating WhatsApp.
- Portfolio: double-tier segmented filter (market: all/arab/foreign; category: all/websites/stores/other), responsive card grid with empty state.
- Consultation form posting to backend leads.
- Contact section: 3 cards (phone, support, email) + minimalist footer.
- Admin dashboard at /admin (JWT) with full CRUD for projects (image upload via Object Storage), site settings editor (agency name, phone, whatsapp, support phone, email, logo upload), and leads inbox.

## Architecture
- Backend: FastAPI + MongoDB (motor). JWT (HS256) auth. Object Storage via Emergent Integrations for image uploads.
- Frontend: React 19, react-router 7, Tailwind, shadcn primitives, sonner toasts, Cairo + Tajawal fonts, Lucide icons, custom canvas particle network.

## User Personas
- Public visitor (potential client): browses portfolio, submits consultation request, contacts via phone/whatsapp/email.
- Admin: logs into /admin, manages projects/settings/leads.

## Core Requirements (static)
- Default language Arabic with RTL direction; language toggle to English.
- Contact info fully dynamic (editable in dashboard) – updates everywhere instantly.
- Project upload uses real file storage (not URLs only).
- Live preview URL per project.
- Seed data: 9 sample projects, default settings.

## Implemented (2026-06-06)
- ✅ Backend: auth (login/me/logout), settings GET/PUT + logo upload, projects CRUD with multipart file upload, leads create/list/delete/patch, file serving via /api/files/{path}.
- ✅ Object storage integration with EMERGENT_LLM_KEY.
- ✅ Seed admin user (admin@mergent.com / Admin@123), default settings, 9 sample projects with external image fallbacks.
- ✅ Frontend public site: Header (logo, lang toggle, hamburger drawer), Hero (particle field + AI badge + headline + 2 stacked CTAs), Portfolio (double-tier filters + grid + empty state), Consultation form, Contact 3-cards, Footer, Floating WhatsApp.
- ✅ i18n (AR default RTL, EN secondary LTR) with persistence.
- ✅ Admin dashboard: login, projects CRUD with image upload, settings editor + logo upload, leads inbox table.
- ✅ Tests passing: backend 13/13 (pytest), frontend Playwright flows verified.

## Updated (2026-06-06 — Iteration 3: Full platform integration)
- ✅ **Auto language detection** in `LangContext`: navigator.language → ar (when AR locale or region) else en; manual toggle overrides and persists in localStorage `mergent_lang`.
- ✅ **SEO/OG/Twitter/JSON-LD** meta tags added to `public/index.html` (NUVORA branding, OG image, canonical, Organization schema).
- ✅ **Lead notifications**: env-driven Telegram + SMTP (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SMTP_HOST/PORT/USER/PASS`, `NOTIFY_EMAIL`). Runs as FastAPI `BackgroundTasks` so POST `/api/leads` stays fast even when keys are added later. No-op when keys are empty.
- ✅ **Lead status workflow**: PATCH `/api/leads/{id}` validates status ∈ {new, contacted, won, lost}. Admin Leads table now exposes per-row colored status badge + dropdown select that PATCHes in place.
- ✅ **Hero EN single-line**: `clamp(2.6rem, 13vw, 9rem)` + `whiteSpace: nowrap`. Verified one-line at 1920px and 390px viewports.
- ✅ **3-icon radial Contact bar** (Phone / Headset→WhatsApp / Mail) replaces boxed cards. Color-matched to deep teal NUVORA palette. data-testid: `icon-call`, `icon-support`, `icon-email`.
- ✅ Tests passing: backend 23/23 pytest, Playwright e2e clean (zero UI/integration/design issues).

## Updated (2026-06-06 — Iteration 2: NUVORA rebrand)
- ✅ Global rename to **NUVORA** (header, drawer, admin shell, public/index.html title, footer copyright, default settings).
- ✅ Floating WhatsApp button color changed from green to deep teal `#0A3D42` (NUVORA brand).
- ✅ Footer rebuilt as minimalist: brand block + 3 clickable contact rows (`tel:`, `mailto:`, `https://wa.me/`) with tight, sleek small copyright row.
- ✅ Bilingual portfolio schema (`title_ar`, `title_en`, `description_ar`, `description_en`); admin ProjectForm exposes all 4 fields; portfolio cards swap language on toggle.
- ✅ Tests passing: backend 15/15 (pytest), Playwright e2e clean (no UI bugs, no design issues).

## Test Credentials
See `/app/memory/test_credentials.md`.

## Backlog / Next Action Items
- P1: Add SEO meta tags (Open Graph) and favicon for the agency.
- P1: Email notification when a new lead arrives (e.g., Resend/SendGrid).
- P2: Lead status workflow (new → contacted → won/lost) with PATCH already exposed.
- P2: Add WhatsApp chatbot template messages.
- P3: Multi-admin user management + role-based permissions.
- P3: Analytics dashboard for leads-per-week, top services.

## File Map
- Backend: `/app/backend/server.py`
- Frontend pages: `/app/frontend/src/pages/{Home,AdminLogin,AdminDashboard}.jsx`
- Frontend components: `/app/frontend/src/components/{Header,Hero,Portfolio,ConsultationForm,Contact,Footer,FloatingWhatsApp,DrawerMenu,ParticleField}.jsx`
- Contexts: `/app/frontend/src/contexts/{LangContext,SettingsContext,AuthContext}.jsx`
- i18n: `/app/frontend/src/i18n.js`
