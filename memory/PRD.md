# Fakulti CRM - Product Requirements Document

## Original Problem Statement
Build a comprehensive CRM and sales funnel automation platform for "Fakulti" brand (supplements company in Ecuador). The system manages leads, automates sales funnel stages, integrates gamification, handles quotations, and manages post-sale loyalty sequences.

## Core Requirements
- **AI Agent**: Virtual assistant using GPT-5.2 for lead qualification, quoting, and sales
- **Intelligent Funnel**: Automated lead categorization (Prospecto → Interesado → En Negociación → Cliente → Perdido)
- **CRM Panel**: Full admin dashboard with metrics, lead management, bulk operations
- **Gamification**: Roulette, Slot Machine, Scratch Card games for lead engagement
- **Loyalty System**: Configurable post-sale messaging sequences (up to 24 messages)
- **Quote Generation**: PDF quotation generation and download
- **WhatsApp Integration**: Webhook for incoming messages with auto-greeting and lead registration

## Tech Stack
- **Frontend**: React, Tailwind CSS, Shadcn/UI, Recharts
- **Backend**: FastAPI, Motor (async MongoDB), Pydantic
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
- **Database**: MongoDB

## User Credentials
- Admin: admin@faculty.com / admin123

## What's Been Implemented

### Completed Features
1. **Dashboard** - KPI cards, funnel visualization, charts (products, traffic sources), recent leads
2. **Lead Management** - CRUD, search, filter by stage/source, stage change dropdown, detail view
3. **Gamification** - Roulette, Slot Machine, Scratch Card with public-facing pages
4. **AI Chat** - GPT-5.2 powered assistant with auto lead registration and stage classification
5. **Quotations** - Create quotations, PDF generation and download
6. **Bulk Operations** - Excel upload/download with duplicate detection
7. **Light/Dark Mode** - System-wide theme toggle (light default)
8. **WhatsApp Webhook** - New/returning lead greeting, name registration, auto-staging by keywords
9. **Lead Stage Renaming** - "En Negociación" and "Perdido" replacing old names, with DB migration
10. **Chat Delete Functions** - Delete individual messages and clear entire conversations
11. **Loyalty System** - Sequence CRUD, lead enrollment, auto-enrollment on purchase, message processing with progress tracking
12. **Loyalty Metrics Dashboard** - Repurchase rates, retention rates, revenue by product, sequence effectiveness, top buyers with charts
13. **Custom Branding** - Fakulti title, Emprenovus footer, hidden Emergent badge

### Funnel Stages
- `nuevo`, `interesado`, `en_negociacion`, `cliente_nuevo`, `cliente_activo`, `perdido`

## Architecture
```
/app/backend/server.py     - All API routes, models, startup seed
/app/frontend/src/
  App.js                   - Router, Auth, Theme providers
  pages/
    DashboardPage.jsx      - Dashboard with metrics
    LeadsPage.jsx          - Lead management
    ChatPage.jsx           - AI chat with delete functions
    LoyaltyPage.jsx        - Sequences + Enrollments with tabs
    QuotationsPage.jsx     - Quote creation + PDF
    BulkPage.jsx           - Excel upload/download
    GamesConfigPage.jsx    - Game configuration
    GamePublicPage.jsx     - Public game pages
    LoginPage.jsx          - Authentication
    SettingsPage.jsx       - Settings
  components/
    Sidebar.jsx            - Navigation
    Footer.jsx             - Custom footer
```

## Pending / Future Tasks
- **P2: Fibeca QR Code Flow** - Journey for physical store customers scanning QR
- **P2: Human Agent Handover** - Pause automation and alert human agent
- **P3: Real WhatsApp API** - Connect webhook to actual WhatsApp Business API
- **P3: Scheduled Loyalty Processing** - Background job for automatic message sending

## MOCKED Integrations
- WhatsApp webhook is standalone (not connected to WhatsApp Business API)
- Loyalty message delivery is simulated (logged, marked as sent in DB)
