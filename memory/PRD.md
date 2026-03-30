# Fakulti CRM - PRD

## Problema Original
Plataforma CRM completa con automatización de ventas por WhatsApp para la marca "Fakulti". Incluye tracking de leads, bots de IA por producto, campañas masivas, gamificación y reportes.

## Stack Técnico
- **Frontend**: React, Tailwind, Shadcn UI
- **Backend**: FastAPI, MongoDB (Motor)
- **AI**: GPT-5.2 via emergentintegrations (v0.1.1)
- **WhatsApp**: Meta Cloud API v25.0

## Flujo WhatsApp (Prioridad Máxima)
El flujo bidireccional de mensajes WhatsApp está **completamente funcional y probado**:
- Webhook Meta procesa todos los tipos de mensaje (texto, imagen, audio, video, documento, sticker, ubicación, contactos)
- Bot GPT-5.2 fluido, inteligente y con memoria anti-amnesia
- Extracción automática de datos (nombre, ciudad, email, producto, CI/RUC, dirección)
- Progresión automática de funnel stages
- Modo humano: agente puede tomar control directo

## Recordatorios Inteligentes por Etapa (NUEVO)
- **cliente_nuevo/cliente_activo**: Mensajes de soporte post-venta (NO mencionan productos para comprar)
- **interesado/en_negociacion**: Re-engagement mencionando el producto específico del lead
- **nuevo**: Saludo general e invitación a conversar
- Mensajes almacenados en chat_messages con source="reminder"

## Detección de Hot Leads + Campana (NUEVO)
- Cuando un lead alcanza `en_negociacion` o `cliente_nuevo` sin asesor asignado: `needs_advisor=True`
- Notificación automática para admin con tipo "hot_lead"
- Campana titilante sutil (CSS animation) junto al nombre en la sidebar del Chat WhatsApp
- Campana en el header cuando se ve la conversación del hot lead
- La campana desaparece al asignar un asesor humano

## Bloques Completados
Todos los 13 bloques del roadmap + mejoras de recordatorios y hot leads.

## Tareas Canceladas (por instrucción del usuario)
- ~~Flujos de venta IA para 3 productos restantes~~
- ~~Refactoring Frontend~~
- ~~Type hints en Python~~
- ~~Reportes automáticos por email~~
- ~~Deploy Railway~~

## Credenciales de Prueba
- Admin: admin@fakulti.com / admin123
