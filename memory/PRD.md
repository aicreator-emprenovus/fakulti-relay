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
- Phone numbers: Ecuador local format (0XXXXXXXXX), international (593XXXXXXXXX) for API
- Funnel stages: Contacto inicial, Chat, En Negociación, Leads ganados, Cartera activa, Perdido
- Games: standby (only slot_machine active)
- 5 products with independent bot personalities
- Bot pause/resume per lead for human handover
- 1-minute timeout detection triggers handover alerts

## Completed Phases

### Block 1: Configuration & Normalization (2026-03-17)
- [x] Phone normalization Ecuador, stage labels, season/channel fields, games standby, bulk upload

### Block 2: Lead Sources, QR & Channels (2026-03-17)
- [x] QR Campaign CRUD + QR code generation, initial intents, auto-channel detection

### Block 3: Specialized Bots per Product (2026-03-17)
- [x] 5 products with bot_config, product-specific prompts, scan counter

### Block 4: Human Agent Handover (2026-03-17)
- [x] Handover detection: user request keywords + 1-minute timeout (3+ messages, still "nuevo" stage)
- [x] Pause/resume bot per lead (PUT /api/leads/{id}/pause-bot, /resume-bot)
- [x] When bot paused: messages still stored in chat history, but no GPT auto-reply
- [x] Handover alerts enriched with: reason, product, channel, city, stage, bot_paused
- [x] "Tomar Control" / "Reactivar Bot" buttons in WhatsApp Bot UI
- [x] Bot status indicator: "Bot activo (especializado en X)" or "Modo humano activo"
- [x] "HUMANO" badge in session list, "BOT PAUSADO" header indicator
- [x] Alert panel with reason labels, product/channel/city badges, take-over button
- [x] Lead context header: name, stage, phone, city, product_interest

### Previously Completed
- [x] Live WhatsApp Integration & Bot Intelligence (GPT-5.2)
- [x] WhatsApp Chat Monitor, Gamification UI, Excel Reporting
- [x] Spanish orthography, Full responsiveness, CRM Dashboard

## Upcoming Tasks

### Block 5: Advisor Registration & Management (P1)
- [ ] Advisor module in admin panel (name, WhatsApp, status, availability)
- [ ] Lead/conversation assignment to advisors
- [ ] Role-based permissions (advisor sees only their data)
- [ ] Notification when assigned lead writes again

### Block 6: Internal Alerts (P2)
- [ ] Visual alerts with blinking + sound on/off toggle
- [ ] Alert routing to assigned advisor

### Block 7: Lead Panel Changes (P2)
- [ ] Filter by advisor in lead search

### Block 8: WhatsApp Bot with Client Context (P2)
- [ ] Client card visible at top of conversation (PARTIALLY DONE - header shows context)
- [ ] Advisor profile sees only assigned conversations

### Block 9: Loyalty & Automations (P2)
- [ ] Auto-follow-up 200h, per-advisor automation

### Block 10: Promotions & Campaigns (P3)
- [ ] "Promociones" admin tab, AI images, templates

### Block 11: Bulk Upload & Batch Reminders (P3)
- [ ] Controlled batch sending with pause/continue

### Block 12: Admin Dashboard by Advisor (P3)
- [ ] Sales by advisor charts

### Block 13: AI Conversation Analysis (P3)
- [ ] AI classifies lead progress, suggests responses

## Credentials
- CRM Login: admin@fakulti.com / admin123
