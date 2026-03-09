# Fakulti CRM - Product Requirements Document

## Original Problem Statement
Build a comprehensive CRM and sales funnel automation platform for "Fakulti" brand (supplements company in Ecuador). The system manages leads, automates sales funnel stages, integrates gamification, handles quotations, and manages post-sale loyalty sequences.

## Core Requirements
- **AI Agent**: Virtual assistant using GPT-5.2 via WhatsApp for lead qualification, product education, and sales
- **Intelligent Funnel**: Automated lead categorization (Nuevo > Interesado > En Negociacion > Cliente Nuevo > Cliente Activo > Perdido)
- **CRM Panel**: Full admin dashboard with metrics, lead management, bulk operations
- **Gamification**: Roulette, Slot Machine, Scratch Card games for lead engagement
- **Loyalty System**: Configurable post-sale messaging sequences (up to 24 messages)
- **WhatsApp Integration**: Real WhatsApp Cloud API via Meta with GPT-5.2 powered bot
- **Automation Panel**: Rules engine for bot behavior management

## Tech Stack
- **Frontend**: React, Tailwind CSS, Shadcn/UI, Recharts, react-beautiful-dnd
- **Backend**: FastAPI, Motor (async MongoDB), Pydantic, httpx
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
- **Database**: MongoDB
- **External**: WhatsApp Cloud API (Meta), Railway relay service

## User Credentials
- Admin: admin@fakulti.com / admin123

## What's Been Implemented

### Completed Features
1. **Dashboard** - KPI cards, funnel visualization, charts (products, traffic sources), recent leads
2. **Lead Management** - Kanban board with 6 stage columns, drag-and-drop, lead cards with action icons
3. **Gamification** - Roulette, Slot Machine, Scratch Card with public-facing pages
4. **Light/Dark Mode** - System-wide theme toggle
5. **WhatsApp Bot (GPT-5.2)** - FULLY WORKING. Conversational AI bot that:
    - Greets new users and asks name naturally
    - Follows Faculty brand voice (natural, cercano, humano, profesional)
    - Explains Bone Broth Hidrolizado (Bombro) product in simple terms
    - Asks qualification questions naturally during conversation
    - Auto-extracts: nombre, apellido, ciudad, email, producto de interes
    - Auto-classifies funnel stage based on conversation context
    - Maintains conversation history for context
    - Never makes medical claims
    - Responds in short messages (1-4 lines)
6. **WhatsApp Monitor** - Real-time CRM view with:
    - Stats bar (Active convos 24h, Avg response time, Messages today, Alerts)
    - All WhatsApp conversations visible
    - CRM agent can reply directly to any WhatsApp conversation
    - Human handover alerts with resolve functionality
    - Auto-refresh every 8 seconds
    - Response time tracking
7. **Loyalty System** - Sequence CRUD, enrollment, auto-enrollment, metrics dashboard
8. **Configuracion Panel** - Automation rules, WhatsApp credentials, AI settings
9. **Custom Branding** - Fakulti title, Emprenovus footer

### Funnel Stages
- `nuevo`, `interesado`, `en_negociacion`, `cliente_nuevo`, `cliente_activo`, `perdido`

## Architecture
```
/app/backend/server.py     - All API routes, models, AI bot logic
/app/frontend/src/
  App.js                   - Router, Auth, Theme providers
  pages/
    DashboardPage.jsx      - Dashboard with metrics
    LeadsPage.jsx          - Kanban board lead management
    ChatPage.jsx           - WhatsApp Bot monitor (ONLY WhatsApp, no internal chat)
    LoyaltyPage.jsx        - Sequences + Enrollments + Metrics tabs
    BulkPage.jsx           - Excel upload/download (UI pending)
    GamesConfigPage.jsx    - Game configuration
    GamePublicPage.jsx     - Public game pages
    ConfigPage.jsx         - Automation, WhatsApp, AI settings
    LoginPage.jsx          - Authentication
    AdminLayout.jsx        - Main layout wrapper
  components/
    Sidebar.jsx            - Navigation (shows "WhatsApp Bot")
    Footer.jsx             - Custom footer
```

## WhatsApp Architecture
- **Railway Relay**: `https://relay-production-8a3a.up.railway.app`
- **Railway Variables**: BACKEND_URL and TARGET_URL = base URL only (no path suffix)
- **Credentials**: MongoDB `whatsapp_config` collection
- **Phone Number ID**: 994356967089829
- **Flow**: User WhatsApp -> Meta -> Railway Relay -> Backend /api/webhook/whatsapp -> GPT-5.2 -> WhatsApp API
- **Bot Prompt**: Detailed Faculty brand voice with product knowledge, conversational flow, and automatic data extraction
- **Data Extraction Tags**: [LEAD_NAME:], [UPDATE_LEAD:field=value], [STAGE:stage] - parsed by backend, stripped before sending

## Pending / Future Tasks
- **P1: Excel Bulk Upload/Download** - Implement functionality on BulkPage.jsx
- **P2: Fibeca QR Code Flow** - Journey for physical store QR scanning
- **P2: Human Agent Handover** - Full pause/resume automation
- **P3: Scheduled Loyalty Processing** - Background job

## LIVE Integrations
- WhatsApp Cloud API via Meta (LIVE)
- OpenAI GPT-5.2 via Emergent LLM Key (LIVE)

## MOCKED Integrations
- Loyalty message delivery (logged in DB, not actually sent)
