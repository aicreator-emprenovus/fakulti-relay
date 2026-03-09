# Fakulti CRM - Product Requirements Document

## Original Problem Statement
Build a comprehensive CRM and sales funnel automation platform for "Fakulti" brand (supplements company in Ecuador). The system manages leads, automates sales funnel stages, integrates gamification, handles quotations, and manages post-sale loyalty sequences.

## Core Requirements
- **AI Agent**: Virtual assistant using GPT-5.2 for lead qualification, quoting, and sales
- **Intelligent Funnel**: Automated lead categorization (Nuevo > Interesado > En Negociacion > Cliente Nuevo > Cliente Activo > Perdido)
- **CRM Panel**: Full admin dashboard with metrics, lead management, bulk operations
- **Gamification**: Roulette, Slot Machine, Scratch Card games for lead engagement
- **Loyalty System**: Configurable post-sale messaging sequences (up to 24 messages)
- **WhatsApp Integration**: Real WhatsApp Cloud API via Meta for Developers with live bot
- **Automation Panel**: Rules engine for bot behavior management
- **WhatsApp Monitoring**: Real-time monitoring of WhatsApp conversations, response times, and human handover alerts integrated into Chat IA page

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
2. **Lead Management** - Kanban board with 6 stage columns, drag-and-drop, lead cards with action icons, search and filters
3. **Gamification** - Roulette, Slot Machine, Scratch Card with public-facing pages
4. **AI Chat** - GPT-5.2 powered assistant with auto lead registration and stage classification
5. **Light/Dark Mode** - System-wide theme toggle (light default)
6. **WhatsApp Live Integration** - FULLY WORKING. Real WhatsApp Cloud API via Meta, Railway relay for webhook forwarding, auto-greeting, name registration, auto-staging by keywords
7. **Lead Stage Renaming** - "En Negociacion" and "Perdido" stages with DB migration
8. **Chat Delete Functions** - Delete individual messages and clear entire conversations
9. **Loyalty System** - Sequence CRUD, lead enrollment, auto-enrollment on purchase, message processing with progress tracking
10. **Loyalty Metrics Dashboard** - Repurchase rates, retention rates, revenue by product, sequence effectiveness, top buyers with charts
11. **Custom Branding** - Fakulti title, Emprenovus footer
12. **Configuracion Panel** - 3 tabs: Automatizacion (bot rules CRUD), WhatsApp Business Cloud API (credentials, webhook), IA config (feature toggles)
13. **WhatsApp Real-Time Monitor** - Integrated into Chat IA page with:
    - Stats bar (Active convos 24h, Avg response time, Messages today, Pending alerts)
    - Session filters (All/WhatsApp/Chat IA)
    - WhatsApp sessions with WA badge and EN VIVO indicator
    - Human handover detection (keywords: agente, humano, persona real, etc.)
    - Alert panel for pending human handover requests
    - CRM agent can reply directly to WhatsApp conversations
    - Auto-refresh every 10 seconds for new messages
    - Response time tracking on WhatsApp bot responses

### Funnel Stages
- `nuevo`, `interesado`, `en_negociacion`, `cliente_nuevo`, `cliente_activo`, `perdido`

## Architecture
```
/app/backend/server.py     - All API routes, models, startup seed
/app/frontend/src/
  App.js                   - Router, Auth, Theme providers
  pages/
    DashboardPage.jsx      - Dashboard with metrics
    LeadsPage.jsx          - Kanban board lead management
    ChatPage.jsx           - AI chat + WhatsApp real-time monitor
    LoyaltyPage.jsx        - Sequences + Enrollments + Metrics tabs
    BulkPage.jsx           - Excel upload/download (UI pending)
    GamesConfigPage.jsx    - Game configuration
    GamePublicPage.jsx     - Public game pages
    ConfigPage.jsx         - Automation, WhatsApp, AI settings
    LoginPage.jsx          - Authentication
    AdminLayout.jsx        - Main layout wrapper
  components/
    Sidebar.jsx            - Navigation
    Footer.jsx             - Custom footer
```

## WhatsApp Architecture
- **Railway Relay**: `https://relay-production-8a3a.up.railway.app` forwards Meta webhooks to backend
- **Railway Variables**: BACKEND_URL and TARGET_URL must be set to base URL only (no path suffix)
- **Credentials**: Stored in MongoDB `whatsapp_config` collection, managed via /config page
- **Phone Number ID**: 994356967089829
- **Flow**: User WhatsApp -> Meta -> Railway Relay -> Backend /api/webhook/whatsapp -> AI Process -> WhatsApp Cloud API response
- **Handover Detection**: Keywords trigger alerts in `handover_alerts` collection
- **CRM Reply**: Admin can reply via POST /api/chat/whatsapp-reply, message sent directly to user's WhatsApp

## Key API Endpoints
- `/api/chat/whatsapp-stats` - GET WhatsApp monitoring KPIs
- `/api/chat/alerts` - GET human handover alerts
- `/api/chat/alerts/{id}/resolve` - PUT resolve an alert
- `/api/chat/whatsapp-reply` - POST send CRM reply via WhatsApp
- `/api/chat/sessions` - GET all sessions (includes source, lead_phone, has_alert)
- `/api/webhook/whatsapp` - POST receive Meta webhook (with handover detection)

## Pending / Future Tasks
- **P1: Excel Bulk Upload/Download** - Implement functionality on BulkPage.jsx for .xlsx upload and filtered downloads
- **P2: Fibeca QR Code Flow** - Journey for physical store customers scanning QR
- **P2: Human Agent Handover** - Full implementation (pause automation on handover, resume after)
- **P3: Scheduled Loyalty Processing** - Background job for automatic message sending

## LIVE Integrations
- WhatsApp Cloud API via Meta (LIVE, working through Railway relay)
- OpenAI GPT-5.2 via Emergent LLM Key (LIVE)

## MOCKED Integrations
- Loyalty message delivery is simulated (logged, marked as sent in DB)
