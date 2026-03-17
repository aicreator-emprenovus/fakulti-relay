# Fakulti CRM + WhatsApp Bot - Product Requirements Document

## Original Problem Statement
Build a comprehensive CRM and sales funnel automation platform for the brand "Fakulti" (Ecuador-based). The system manages leads, conversations, campaigns, promotions, and human advisors, with specialized bots per product, intelligent handover to human agents, channel segmentation, automations, AI analysis, and campaign reminders.

## Core Architecture
- **Backend**: FastAPI + MongoDB (motor) + Pydantic + JWT auth
- **Frontend**: React + Tailwind CSS + Shadcn/UI + Axios
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
- **External**: WhatsApp Cloud API (via Railway.app relay)
- **DB Collections**: leads, products, games_config, game_plays, quotations, loyalty_sequences, loyalty_enrollments, automation_rules, chat_messages, chat_sessions_meta, admin_users, whatsapp_config, ai_config, handover_alerts, qr_campaigns, initial_intents

## Key Technical Decisions
- Phone numbers: Ecuador local format (0XXXXXXXXX), converted to international (593XXXXXXXXX) for WhatsApp API
- Funnel stages: internal keys, display renamed labels
- Games: standby mode (only slot_machine active)
- Season/channel fields on leads
- QR campaigns auto-detect channel from first WhatsApp message
- 5 products, each with independent bot personality and knowledge base
- Product-specific prompts prevent cross-contamination between bots

## Completed Phases

### Block 1: Configuration & Normalization (2026-03-17)
- [x] Phone normalization Ecuador (no +593 in internal UI)
- [x] Stage labels: Contacto inicial, Chat, En Negociación, Leads ganados, Cartera activa, Perdido
- [x] Season/temporada filter + channel field on leads
- [x] Games standby (only Tragamonedas active)
- [x] Bulk Excel upload with phone normalization, season, channel

### Block 2: Lead Sources, QR & Channels (2026-03-17)
- [x] QR Campaign CRUD + QR code generation (PNG download)
- [x] WhatsApp pre-filled link generation
- [x] Initial Intents CRUD with keyword matching
- [x] Auto-detection of channel from WhatsApp messages
- [x] Channel visible on Lead cards and Chat sessions
- [x] 3 default QR campaigns + 5 default intents

### Block 3: Specialized Bots per Product (2026-03-17)
- [x] 5 products: Bombro, Gomitas Melatonina, CBD Colageno, Pitch Up, Magnesio Citrato
- [x] Each product has bot_config: personality, key_benefits, usage_info, restrictions, faqs
- [x] build_product_bot_prompt() generates product-specific system prompts
- [x] General "router" bot identifies product interest when not yet known
- [x] Once product identified, switches to specialized bot (no cross-contamination)
- [x] Bot config editable per product from admin panel (inline editor)
- [x] QR scan counter: tracks scans per campaign, displayed in cards
- [x] Settings page renamed to "Productos y Bots"

### Previously Completed
- [x] Live WhatsApp Integration & Bot Intelligence (GPT-5.2)
- [x] WhatsApp Chat Monitor with real-time stats
- [x] Gamification UI (Roulette, Slot Machine, Scratch Card)
- [x] Comprehensive Excel Reporting (7-sheet download)
- [x] Spanish orthography corrections system-wide
- [x] Full responsiveness (mobile, tablet, desktop)
- [x] CRM Dashboard, Lead Management, Loyalty System, Automation Rules

## Upcoming Tasks

### Block 4: Human Agent Handover (P1)
- [ ] Handover logic: bot failure, user request, operational rules
- [ ] 1-minute timeout alert for unresolved bot conversations
- [ ] Respect product, assigned advisor, lead history

### Block 5: Advisor Registration & Management (P1)
- [ ] Advisor module in admin panel (name, WhatsApp, status, availability)
- [ ] Lead/conversation assignment to advisors
- [ ] Role-based permissions (advisor sees only their data)
- [ ] Notification when assigned lead writes again

### Block 6: Internal Alerts (P2)
- [ ] Visual alerts with blinking/strong indicators + sound on/off toggle
- [ ] Alert routing to assigned advisor

### Block 7: Lead Panel Changes (P2)
- [ ] Filter by advisor in lead search
- [ ] Lead cards show: channel, city, product interest, email

### Block 8: WhatsApp Bot with Client Context (P2)
- [ ] Client card visible at top of conversation
- [ ] Advisor profile sees only assigned conversations

### Block 9: Loyalty & Automations (P2)
- [ ] Auto-follow-up 200h after loyalty message
- [ ] Per-advisor automation in conversations panel

### Block 10: Promotions & Campaigns (P3)
- [ ] "Promociones" admin tab with campaign creation
- [ ] AI-generated promotional images
- [ ] Quick message templates

### Block 11: Bulk Upload & Batch Reminders (P3)
- [ ] Import historical leads
- [ ] Controlled batch sending with pause/continue

### Block 12: Admin Dashboard by Advisor (P3)
- [ ] Sales by advisor charts/comparisons

### Block 13: AI Conversation Analysis (P3)
- [ ] AI reads conversations, classifies lead progress
- [ ] Suggests next best response for human advisor

## Credentials
- CRM Login: admin@fakulti.com / admin123
- WhatsApp: Managed via Configuración page in CRM
