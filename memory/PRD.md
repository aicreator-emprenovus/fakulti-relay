# Fakulti CRM - PRD

## Original Problem Statement
Plataforma CRM completa con automatizacion de ventas por WhatsApp para la marca "Fakulti". Incluye bot IA con GPT-5.2, gestion de leads, asesores, campanas, recordatorios, juegos de captacion, cotizaciones, sistema de fidelizacion, y panel de desarrollador para entrenamiento del bot.

## Tech Stack
- **Frontend**: React, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python), MongoDB (Motor async)
- **AI**: GPT-5.2 via emergentintegrations (Emergent LLM Key)
- **External API**: Meta WhatsApp Cloud API v25.0 with Message Templates

## Architecture (Post-Refactoring Feb 2026)
```
/app/backend/
├── server.py              # 337 lines - App setup, middleware, startup seed, scheduler
├── database.py            # DB connection (db, client)
├── models.py              # All Pydantic models
├── auth.py                # JWT, password hashing, get_current_user
├── utils.py               # Phone normalization, constants (FUNNEL_STAGES, etc.)
├── whatsapp_utils.py      # WA Cloud API helpers (send_message, send_image, send_template)
├── bot_logic.py           # Shared bot prompt builder (build_product_bot_prompt)
├── routes/
│   ├── auth.py            # Auth routes (login, register, password management)
│   ├── dashboard.py       # Dashboard stats + advisor performance
│   ├── leads.py           # Lead CRUD, stage, assign, purchase, bot pause/resume
│   ├── advisors.py        # Advisor CRUD, notifications (advisor + general)
│   ├── products.py        # Product CRUD, bot config, export/import/delete-all
│   ├── bot_training.py    # Bot Training Center (developer only)
│   ├── games.py           # Games config (roulette, slots, scratch)
│   ├── quotations.py      # Quotation CRUD + PDF
│   ├── loyalty.py         # Loyalty sequences, enrollments, metrics, auto-enroll
│   ├── chat.py            # Chat messages, sessions, alerts, WA monitoring, AI analysis
│   ├── bulk.py            # Bulk upload/download Excel reports
│   ├── whatsapp.py        # WA webhooks, bot logic, upload images
│   ├── automation.py      # Automation rules CRUD, background scheduler
│   ├── config.py          # WA + AI configuration
│   └── campaigns.py       # QR campaigns, promo campaigns, smart reminders
└── tests/                 # Test files
```

## Completed Work
- [x] WhatsApp Cloud API v25.0 integration
- [x] GPT-5.2 AI bot with product-specific and general prompts
- [x] Handover alerts (bot_transfer, solicitud_usuario, timeout)
- [x] Secure password flow (provisional, forced change, strength validation)
- [x] Message Templates for campaigns and reminders
- [x] Automation scheduler (asyncio background task)
- [x] Excel export/import for automation rules
- [x] server.py refactoring: 4647 -> 337 lines (15 route modules)
- [x] Products & Bots: Export/Import Excel + Delete All buttons
- [x] Real-time chat via Server-Sent Events (SSE)
- [x] Audit Log (Historial) section for Admin
- [x] Multimedia attachments via Meta media_id (send & receive)
- [x] Auto-handover when user sends attachment or asks credit-card payment
- [x] Meta Catalog integration (Phase 1 - manual): "Enviar Catálogo" button in chat header sends `interactive: catalog_message` (Ver catálogo button) — uses catalog connected to WABA. catalog_id field added in WhatsApp config panel + diagnose endpoint validates linked catalog. Catalog ID configurado: `1518830646561816`. (2026-04-29)
- [x] Lead stage protection: Leads in "cliente_nuevo" (Leads ganados) and "cliente_activo" (Cartera activa) can NEVER be auto-moved to "perdido" by the bot or automation rules (`sin_respuesta`). Only human advisors can move them manually. Implemented in `routes/whatsapp.py`, `routes/chat.py`, `routes/automation.py` (both run-now + scheduler) using `PROTECTED_FROM_AUTO_LOST` constant in `utils.py`. Validated end-to-end. (2026-05-05)
- [x] Admin user management ("Administradores" menu): admin can create/edit/delete other admins + reset their password from `/admins`. Seed admin (`admin@fakulti.com`) is protected — cannot be deleted nor have its password changed by anyone. Implemented in `routes/admins.py`, `models.AdminCreate`, frontend `AdminsPage.jsx`, sidebar entry above "Asesores". (2026-05-05)
- [x] Audit log redesign: `Historial de actividad` now uses dropdowns instead of free-text inputs (populated from `/api/audit-logs/users` and `/api/audit-logs/actions`). Removed columns "Ruta", "IP", "Estado" — replaced with single "Detalle" column showing affected entity name (lead, asesor, administrador, producto, campaña, regla) using new `entity_type/entity_id/entity_name` fields enriched by audit middleware. (2026-05-05)
- [x] Audit log Stage-Change enrichment (2026-05-05): `PUT /api/leads/{id}/stage` now stashes `audit_details` on `request.state` (e.g. "Lead Pedro Gómez: Chat → En Negociacion"). Server middleware reads `request.state.audit_*` to override the generic entity row. Frontend `renderDetail` prefers `details` over `entity_name`. Audit table column "Acción" now uses `table-fixed` with `w-32 break-words` so long labels wrap to 2 lines.
- [x] Chat improvements (2026-05-05):
  - Removed "Eliminar Chat" button + `DELETE /api/chat/sessions/{id}` endpoint.
  - Removed individual message delete (X overlay) + `DELETE /api/chat/messages/{id}` endpoint.
  - Added BOT / Humano / Todos filter row under "Conversaciones" sidebar (uses `bot_paused` flag).
  - Fixed chat-page height: outer div now uses `h-full flex flex-col` and inner grid uses `flex-1 min-h-0` instead of hardcoded `100vh - 60px`. Chat now fills available space without producing the "bounce/rebote" when scrolling between header and input.

## Backlog
- [ ] Phase 2 catalog: send specific products via `interactive: product` / `product_list` (requires `catalog_id` + `retailer_id` in payload).
- [ ] Component splitting in frontend (ChatPage, LeadsPage, ConfigPage).
- [ ] Type hints across backend Python.
- [ ] Weekly automated email reports for advisors.
