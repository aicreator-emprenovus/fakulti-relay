# Fakulti CRM - Product Requirements Document

## Original Problem Statement
CRM and sales funnel automation platform for "Fakulti" brand. A comprehensive 13-phase plan to upgrade the existing system including lead management, AI WhatsApp bots, advisor management, campaign tools, and analytics.

## Architecture
- **Backend**: FastAPI + MongoDB (motor) + Pydantic + JWT Auth
- **Frontend**: React + Tailwind CSS + Shadcn/UI + Axios
- **External**: WhatsApp Cloud API, OpenAI GPT-5.2 (via Emergent LLM Key)
- **Monolith**: `backend/server.py` (~3100 lines)

## Core Credentials
- Admin: admin@fakulti.com / admin123
- Advisors: carlos@fakulti.com, ana@fakulti.com / advisor123

## ALL 13 Blocks - COMPLETED

### Block 1: General Config & Normalization ✅
- Phone normalization for Ecuador (+593)
- Lead stage renaming, Season filter, Games standby

### Block 2: Lead Sources & QR Codes ✅
- QR campaign management, QR code generation, Lead source tracking, Scan count

### Block 3: Specialized Product Bots ✅
- 5 product-specific AI bot personalities, Auto-routing, Bot config UI

### Block 4: Human Agent Handover ✅
- Keyword/timeout handover, Manual bot pause/resume UI, Handover alerts

### Block 5: Advisor Management ✅
- Full advisor CRUD, RBAC (admin/advisor), Assignment dropdown, Advisor badge on cards

### Block 6: Internal Alerts ✅
- NotificationBell component, Real-time polling, Sound toggle, Visual indicators

### Block 7: Leads Panel UI Changes ✅
- Colored tag badges (channel, source, city, product, advisor), Advisor filter

### Block 8: WhatsApp Bot with Customer Context ✅
- Persistent customer context card in chat header with all lead fields

### Block 9: Fidelización y Automatizaciones ✅ (Completed 2026-03-17)
- Auto-enrollment config (target stage, default sequence)
- Toggle enable/disable, Saves to system_config collection
- New "Auto-Inscripción" tab in Loyalty page

### Block 10: Promociones y Campañas ✅ (Completed 2026-03-17)
- Full campaigns CRUD (create, read, update, delete)
- Target segmentation by stage, product, channel, season
- Batch send via WhatsApp API (preview mode support)
- Stats: total campaigns, sent count, target count, failed count
- Campaign form with message template personalization ({nombre})

### Block 11: Carga Masiva y Recordatorios ✅ (Completed 2026-03-17)
- Full reminders CRUD with batch execution
- Configurable: days since last interaction, batch size, target stage/product
- Historical data upload section on Bulk page
- Execute button sends reminder messages in controlled batches

### Block 12: Dashboard del Administrador ✅ (Completed 2026-03-17)
- "General" and "Por Asesor" tabs on Dashboard
- Advisor metrics: total leads, won, lost, negotiating, revenue, conversion rate
- Summary: total assigned, unassigned, advisors count, total revenue
- Horizontal stacked bar chart per advisor
- Individual advisor cards with all KPIs

### Block 13: IA para Análisis de Conversaciones ✅ (Completed 2026-03-17)
- AI conversation analysis via GPT-5.2 (LlmChat from emergentintegrations)
- Returns: resumen, sentimiento, interes_producto, etapa_sugerida, respuestas_sugeridas, temas_clave, nivel_urgencia
- "IA Análisis" button on Chat page
- Suggested replies clickable to insert into message input
- Analysis panel with color-coded badges

## Key API Endpoints
- `/api/auth/login`, `/api/auth/me` - Authentication
- `/api/leads` - CRUD with role-based filtering
- `/api/leads/{id}/assign` - Assign advisor
- `/api/leads/{id}/pause-bot`, `/api/leads/{id}/resume-bot` - Bot control
- `/api/advisors` - CRUD for advisors
- `/api/chat/sessions`, `/api/chat/history/{id}` - Chat management
- `/api/chat/alerts` - Handover alerts
- `/api/chat/analyze/{session_id}` - AI conversation analysis (Block 13)
- `/api/campaigns` - CRUD for promotional campaigns (Block 10)
- `/api/campaigns/{id}/send` - Send campaign messages (Block 10)
- `/api/reminders` - CRUD for reminders (Block 11)
- `/api/reminders/{id}/execute` - Execute reminder (Block 11)
- `/api/dashboard/stats`, `/api/dashboard/advisor-stats` - Dashboard (Block 12)
- `/api/loyalty/auto-enroll-config` - Auto-enrollment config (Block 9)
- `/api/qr_campaigns` - QR campaign management

## Key Files
- `backend/server.py` - All backend logic (~3100 lines)
- `frontend/src/pages/CampaignsPage.jsx` - Campaign management (Block 10)
- `frontend/src/pages/RemindersPage.jsx` - Reminders management (Block 11)
- `frontend/src/pages/DashboardPage.jsx` - Enhanced with advisor tab (Block 12)
- `frontend/src/pages/ChatPage.jsx` - WhatsApp bot + AI analysis (Blocks 8, 13)
- `frontend/src/pages/LoyaltyPage.jsx` - Auto-enrollment tab (Block 9)
- `frontend/src/pages/LeadsPage.jsx` - Kanban with advisor assignment
- `frontend/src/pages/AdvisorsPage.jsx` - Advisor management
- `frontend/src/components/NotificationBell.jsx` - Alert notifications (Block 6)
- `frontend/src/components/Sidebar.jsx` - Role-aware navigation

## Refactoring Backlog
- Break down `server.py` monolith into modular structure (routes, models, services)
