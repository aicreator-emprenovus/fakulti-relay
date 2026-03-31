# Fakulti CRM - PRD

## Problema Original
Plataforma CRM completa con automatización de ventas por WhatsApp para la marca "Fakulti". Incluye flujo de mensajes bidireccional, recordatorios inteligentes, alertas de leads calientes, roles segregados (Admin, Asesor, Desarrollador), y Centro de Entrenamiento de IA.

## Arquitectura
- Frontend: React + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB (Motor)
- AI: GPT-5.2 via emergentintegrations
- External API: Meta WhatsApp Cloud API v25.0

## Funcionalidades Implementadas
1. WhatsApp Bot bidireccional con Meta Cloud API v25.0
2. AI Bot (GPT-5.2) con historial de conversación y Anti-Amnesia
3. Smart Reminders contextuales por etapa de lead
4. Alerta visual de Lead Caliente (campana pulsante)
5. Roles: Admin, Asesor, Desarrollador
6. Centro de Entrenamiento IA (DevPanelPage)
7. Panel de Alertas para reseteo seguro de contraseñas (DevAlertsPage)
8. Componente PasswordInput reutilizable (ojo toggle)
9. Marca "Fakulti" actualizada globalmente
10. NotificationBell oculto para rol Desarrollador (31 Mar 2026)
11. Fix: Campos de texto del Centro de Entrenamiento - escritura fluida (31 Mar 2026)
12. Fix: Consola de Pruebas aislada de DB real con historial persistente (31 Mar 2026)
13. Feature: Alerta inmediata cuando cliente solicita asesor - detecta tanto keywords del usuario como frases de transferencia del bot (31 Mar 2026)
    - Crea handover_alert en chat con razón (solicitud_usuario / bot_transfer)
    - Crea notificación advisor_request visible en NotificationBell
    - Marca lead como needs_advisor para campanilla de lead caliente
    - Centralizado en process_whatsapp_incoming (funciona en ambos webhooks)

## Backlog Priorizado
### P1
- Configurar flujos de venta IA para 3 productos restantes (BLOQUEADO - requiere input del usuario)
- Dividir componentes grandes del frontend (ChatPage, LeadsPage, ConfigPage)
- Refactorizar server.py (~4000 líneas) en routers modulares

### P2
- Agregar type hints al backend Python
- Reportes automáticos por email semanales para asesores

## Credenciales
- Admin: admin@fakulti.com / admin123
- Developer: aicreator@emprenovus.com / Jlsb*1082
