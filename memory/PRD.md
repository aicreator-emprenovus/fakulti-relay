# Fakulti CRM - Product Requirements Document

## Original Problem Statement
CRM and sales funnel automation platform for "Fakulti" brand. A comprehensive 13-phase plan to upgrade the existing system including lead management, AI WhatsApp bots, advisor management, campaign tools, and analytics.

## Architecture
- **Backend**: FastAPI + MongoDB (motor) + Pydantic + JWT Auth
- **Frontend**: React + Tailwind CSS + Shadcn/UI + Axios
- **External**: WhatsApp Cloud API, OpenAI GPT-5.2 (via Emergent LLM Key)
- **Monolith**: `backend/server.py` (~3260 lines)

## Core Credentials
- Admin: admin@fakulti.com / admin123
- Advisors: carlos@fakulti.com, ana@fakulti.com / advisor123

## ALL 13 Blocks - COMPLETED

### Block 1-8: Previously Completed ✅
### Block 9-13: Completed in previous session ✅

### Product Bot Configuration - Bone Broth ✅ (Completed 2026-03-17)
- Full sales flow script (3267 chars) loaded into bot_config.sales_flow
- 9-stage sales funnel: Hook → Intent Classification → Education → Qualification → Recommendation → Offer → Objection Handling → Close → Follow-up
- Intent detection: Digestion, Articulaciones, Energia, Info general
- Objection handling: Price, pharmacy comparison, "I'll think about it"
- Data extraction: name, CI/RUC, email, address, city
- New fields: ci_ruc, address in LeadUpdate model
- Settings UI: New "Flujo de Ventas Avanzado" textarea field
- Enhanced build_product_bot_prompt: Uses sales_flow when present, falls back to simple prompt

## Key API Endpoints
- All previous endpoints remain
- `/api/products/{id}/bot-config` - Now supports `sales_flow` field

## Product Bot Status
- **Bombro - Bone Broth Hidrolizado**: ✅ Full sales flow configured
- **Gomitas Melatonina**: Basic config (needs sales flow)
- **Gomitas Biotina**: Basic config (needs sales flow)
- **Colágeno Hidrolizado**: Basic config (needs sales flow)
- **Magnesio Citrato**: Basic config (needs sales flow)

## Pending
- Configure sales flows for remaining 4 products (user to provide scripts)
- Refactoring: Break server.py monolith into modules
