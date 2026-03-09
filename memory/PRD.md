# Fakulti CRM - Product Requirements Document

## Original Problem Statement
Build a comprehensive CRM and sales funnel automation platform for "Fakulti" brand (supplements company in Ecuador). The system manages leads, automates sales funnel stages, integrates gamification, handles quotations, and manages post-sale loyalty sequences.

## Core Requirements
- **AI Agent**: Virtual assistant using GPT-5.2 via WhatsApp for lead qualification, product education, and sales
- **Intelligent Funnel**: Automated lead categorization (Nuevo > Interesado > En Negociacion > Cliente Nuevo > Cliente Activo > Perdido)
- **CRM Panel**: Full admin dashboard with metrics, lead management, bulk operations
- **Gamification**: Premium Roulette, Slot Machine, and Golden Ticket (scratch card) games
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
3. **Gamification (Premium UI)** - Three games with product images:
    - **Ruleta**: Dark premium design, LED lights ring, neon segment colors, product images in segments, FAKULTI center, glowing CTA button
    - **Tragamonedas**: Casino-style with red marquee sign, gold rivets, real product images in reels (Bombro, Gomitas, etc.), red payline, decorative lights
    - **Golden Ticket**: Willy Wonka style scratch card, golden gradient with shimmer animation, perforated border, coin cursor for scratching, star decorations
4. **Light/Dark Mode** - System-wide theme toggle
5. **WhatsApp Bot (GPT-5.2)** - FULLY WORKING with detailed Faculty brand voice prompt:
    - Natural, human-like conversation flow
    - Auto-extracts: nombre, apellido, ciudad, email, producto de interes
    - Auto-classifies funnel stage
    - Explains Bone Broth in simple terms
    - Never makes medical claims
    - Permanent token configured
6. **WhatsApp Monitor** - Real-time CRM view with stats, alerts, CRM agent reply
7. **Loyalty System** - Sequence CRUD, enrollment, auto-enrollment, metrics dashboard
8. **Configuracion Panel** - Automation rules, WhatsApp credentials, AI settings
9. **Custom Branding** - Fakulti title, Emprenovus footer

### Funnel Stages
- `nuevo`, `interesado`, `en_negociacion`, `cliente_nuevo`, `cliente_activo`, `perdido`

## Architecture
```
/app/backend/server.py     - All API routes, models, AI bot logic
/app/frontend/src/
  pages/
    DashboardPage.jsx      - Dashboard
    LeadsPage.jsx          - Kanban board
    ChatPage.jsx           - WhatsApp Bot monitor (WhatsApp only)
    LoyaltyPage.jsx        - Loyalty system
    BulkPage.jsx           - Excel upload/download (UI pending)
    GamesConfigPage.jsx    - Game configuration
    GamePublicPage.jsx     - Premium game UIs (roulette, slot, scratch)
    ConfigPage.jsx         - Settings
    LoginPage.jsx          - Auth
```

## WhatsApp Architecture
- **Railway Relay**: `https://relay-production-8a3a.up.railway.app`
- **WABA ID**: 1445540157191817 (subscribed to Fakulti Bot app)
- **Phone Number ID**: 994356967089829
- **Token**: Permanent system user token
- **Flow**: WhatsApp -> Meta -> Railway -> Backend -> GPT-5.2 -> WhatsApp API

## Pending / Future Tasks
- **P1: Excel Bulk Upload/Download** - BulkPage.jsx
- **P2: Fibeca QR Code Flow** - Physical store QR journey
- **P2: Human Agent Handover** - Full pause/resume automation
- **P3: Scheduled Loyalty Processing** - Background job

## LIVE Integrations
- WhatsApp Cloud API via Meta (LIVE, permanent token)
- OpenAI GPT-5.2 via Emergent LLM Key (LIVE)

## MOCKED Integrations
- Loyalty message delivery (logged in DB, not actually sent via WhatsApp)
