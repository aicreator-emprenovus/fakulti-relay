# Fakulti CRM - PRD

## Problema Original
Plataforma CRM completa con automatización de ventas por WhatsApp para la marca "Fakulti". Incluye tracking de leads, bots de IA por producto, campañas masivas, gamificación y reportes.

## Stack Técnico
- **Frontend**: React, Tailwind, Shadcn UI
- **Backend**: FastAPI, MongoDB (Motor)
- **AI**: GPT-5.2 via emergentintegrations (v0.1.1)
- **WhatsApp**: Meta Cloud API v25.0

## Estado Actual - Flujo WhatsApp
El flujo bidireccional de mensajes WhatsApp está **completamente funcional y probado (20/20 tests)**:
- Webhook Meta procesa mensajes de texto, imagen, audio, video, documento, sticker, ubicación, contactos
- Status updates (delivery receipts) se ignoran silenciosamente
- Bot GPT-5.2 responde con fluidez natural en español
- Anti-amnesia: el bot recuerda datos del cliente a lo largo de la conversación
- Extracción automática de nombre, ciudad, email, producto de interés, CI/RUC, dirección
- Progresión automática de funnel stages
- Modo humano: agente puede tomar control y responder directamente por WhatsApp
- Endpoint legacy para testing almacena mensajes y session meta correctamente

## Bloques Completados (1-13)
Todos los 13 bloques del roadmap implementados y testeados.

## Cambios Recientes
### 30/03/2026 - Flujo WhatsApp (Prioridad Máxima)
- **Meta API v25.0**: Actualizada desde v22.0 (y corregido v21.0 hardcodeado en recordatorios)
- **emergentintegrations v0.1.1**: Actualizada desde v0.1.0
- **Webhook multi-tipo**: Ahora maneja imagen, audio, video, documento, sticker, ubicación, contactos (antes solo texto)
- **Status updates**: Delivery receipts de Meta se ignoran silenciosamente (antes generaban logs innecesarios)
- **Session meta**: lead_name ahora se resuelve correctamente (antes siempre vacío en webhook)
- **Legacy endpoint mejorado**: Ahora almacena mensajes y session meta (antes solo procesaba sin guardar)
- **send_whatsapp_message**: Acepta 200 y 201 (antes solo 200)
- **Bug fix: missing_instruction**: Instrucciones de datos faltantes ahora incluidas en prompts del bot (antes se construían pero nunca se usaban)
- **Recordatorios**: Reutilizan send_whatsapp_message en vez de código duplicado con versión API vieja

### 30/03/2026 - Anteriores
- Code Quality Refactoring, Anti-Amnesia, Campañas WhatsApp, etc. (ver CHANGELOG)

## Tareas Canceladas (por instrucción del usuario)
- ~~P1: Flujos de venta IA para 3 productos restantes~~
- ~~P1: Refactoring Frontend (ChatPage.jsx, LeadsPage.jsx)~~
- ~~P1: Type hints en Python~~
- ~~P2: Reportes automáticos por email~~
- ~~P2: Deploy Railway~~

## Credenciales de Prueba
- Admin: admin@fakulti.com / admin123
