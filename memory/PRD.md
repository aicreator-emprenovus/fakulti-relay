# Fakulti CRM - Product Requirements Document

## Original Problem Statement
CRM and sales funnel automation platform for "Fakulti" brand. A comprehensive 13-phase plan to upgrade the existing system including lead management, AI WhatsApp bots, advisor management, campaign tools, and analytics.

## Architecture
- **Backend**: FastAPI + MongoDB (motor) + Pydantic + JWT Auth
- **Frontend**: React + Tailwind CSS + Shadcn/UI + Axios
- **External**: WhatsApp Cloud API, OpenAI GPT-5.2 (via Emergent LLM Key)
- **Monolith**: `backend/server.py` (~2860 lines)

## Core Credentials
- Admin: admin@fakulti.com / admin123
- Advisors: carlos@fakulti.com, ana@fakulti.com / advisor123

## Completed Phases

### Block 1: General Config & Normalization ✅
- Phone normalization for Ecuador (+593)
- Lead stage renaming (Contacto inicial, Chat, En Negociación, etc.)
- Season filter (verano, invierno, todo el año)
- Games on standby (only slot_machine active)

### Block 2: Lead Sources & QR Codes ✅
- "QR y Canales" page for QR campaign management
- QR code generation per campaign
- Lead source tracking by channel
- Scan count tracking

### Block 3: Specialized Product Bots ✅
- 5 product-specific AI bot personalities
- Auto-routing to correct product bot
- Bot configuration UI in Settings page

### Block 4: Human Agent Handover ✅
- Keyword-triggered handover
- 1-minute bot response timeout detection
- Manual "Tomar Control" / "Reactivar Bot" UI
- Handover alert system

### Block 5: Advisor Management ✅ (Completed 2026-03-17)
- Full advisor CRUD (create, read, update, delete)
- Role-based access control (admin vs advisor)
- Advisor assignment dropdown in lead detail dialog
- Advisor name badge on lead cards (orange)
- Role-based filtering: advisors only see assigned leads/conversations
- Advisor filter in leads search bar

### Block 6: Internal Alerts ✅ (Completed 2026-03-17)
- NotificationBell component in top bar (all pages)
- Real-time polling for handover alerts + advisor notifications
- Sound toggle with localStorage persistence
- Visual indicator (red badge with count, pulse animation)
- Mark as read / mark all read functionality

### Block 7: Leads Panel UI Changes ✅ (Completed 2026-03-17)
- Lead cards show colored tag badges (channel, source, city, product, advisor)
- Advisor filter dropdown for admin users
- Stage labels properly renamed

### Block 8: WhatsApp Bot with Customer Context ✅ (Completed 2026-03-17)
- Persistent customer context card in chat header
- Shows: Tel, Email, Ciudad, Fuente, Canal, Producto, Temporada, Asesor
- Loads via GET /api/leads/{lead_id} with _advisor_name

## Upcoming Tasks (Prioritized Backlog)

### P0 - Block 9: Fidelización y Automatizaciones
- Post-sale follow-up sequence enhancement
- Loyalty program features

### P1 - Block 10: Promociones y Campañas
- Campaign creation and management module
- Auto-generated promotional images
- Campaign sending system

### P1 - Block 11: Carga Masiva y Recordatorios
- Enhanced bulk upload for historical data
- Controlled, batched reminder campaign system

### P2 - Block 12: Dashboard del Administrador
- Sales and performance metrics per advisor
- Dashboard revamp with analytics

### P2 - Block 13: IA para Análisis de Conversaciones
- AI conversation summarization
- Suggested replies for human agents

## Refactoring Backlog
- Break down `server.py` monolith into modular structure (routes, models, services)

## Key API Endpoints
- `/api/auth/login`, `/api/auth/me` - Authentication
- `/api/leads` - CRUD with role-based filtering
- `/api/leads/{id}/assign` - Assign advisor to lead
- `/api/leads/{id}/pause-bot`, `/api/leads/{id}/resume-bot` - Bot control
- `/api/advisors` - CRUD for advisors
- `/api/advisors/notifications` - Notification polling
- `/api/chat/sessions`, `/api/chat/history/{id}` - Chat management
- `/api/chat/alerts` - Handover alerts
- `/api/qr_campaigns` - QR campaign management
- `/api/products/{id}/bot_config` - Bot configuration

## Key Files
- `backend/server.py` - All backend logic
- `frontend/src/pages/LeadsPage.jsx` - Kanban board with advisor assignment
- `frontend/src/pages/ChatPage.jsx` - WhatsApp bot monitor with context card
- `frontend/src/pages/AdvisorsPage.jsx` - Advisor management
- `frontend/src/components/NotificationBell.jsx` - Alert notification system
- `frontend/src/components/Sidebar.jsx` - Role-aware navigation
- `frontend/src/App.js` - Routes and layout with NotificationBell
