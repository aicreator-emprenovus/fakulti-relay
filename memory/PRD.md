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
│   ├── products.py        # Product CRUD, bot config per product
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

## User Roles
1. **Developer** (aicreator@emprenovus.com) - Full access, bot training, admin management
2. **Admin** (admin@fakulti.com) - CRM management, campaigns, advisor management
3. **Advisor** - Assigned lead conversations only

## Key Features Implemented
- Bi-directional WhatsApp integration via Meta Cloud API v25.0
- AI Bot with GPT-5.2: Anti-Amnesia, Smart product-specific prompts
- Hot Lead alerts + Handover detection (bot_transfer, solicitud_usuario)
- Forced password change on first login with provisional passwords
- Message Template support for campaigns and reminders (24h rule bypass)
- Background async scheduler for automation rules (every 30 min)
- Excel Export/Import for automation rules and bulk leads
- Lead deduplication and phone normalization on startup
- QR campaign tracking with automatic channel detection
- Loyalty sequences with WhatsApp delivery
- Full Excel reporting with 7-sheet executive reports

## Completed Work
- [x] WhatsApp Cloud API v25.0 integration
- [x] GPT-5.2 AI bot with product-specific and general prompts
- [x] Handover alerts (bot_transfer, solicitud_usuario, timeout)
- [x] Secure password flow (provisional, forced change, strength validation)
- [x] Message Templates for campaigns and reminders
- [x] Automation scheduler (asyncio background task)
- [x] Excel export/import for rules
- [x] **server.py refactoring: 4647 -> 337 lines (15 route modules)**

## Backlog (Cancelled by User)
- Configure AI Sales Flows for remaining 3 products (needs user scripts)
- Frontend component splitting (ChatPage, LeadsPage, ConfigPage)
- Type hints for Python backend
- Automated email reports for advisors
