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
7. Panel de Alertas con generación de contraseñas provisionales
8. Componente PasswordInput reutilizable
9. Marca "Fakulti" actualizada globalmente
10. NotificationBell oculto para rol Desarrollador
11. Fix: Centro de Entrenamiento escritura fluida + Consola de Pruebas aislada
12. Feature: Alerta inmediata cuando cliente solicita asesor
13. Feature: Flujo completo de contraseñas provisionales
14. Bugfix: Campañas/Recordatorios verifican entrega real WhatsApp
15. Feature: Soporte de Message Templates de Meta en campañas y recordatorios
16. Feature: Scheduler automático de recordatorios (10 Apr 2026)
    - Proceso background que corre cada 30 min
    - Procesa reglas tipo "sin_respuesta" automáticamente
    - Envía recordatorios a leads sin interacción (4h, 24h)
    - Cambia etapa a "perdido" después de 48h sin respuesta
    - Soporte de templates de Meta para mensajes fuera de 24h
    - Log de automatización (automation_log) para trazabilidad
    - Endpoint /automation/run-now para ejecución manual
    - Botón "Ejecutar Ahora" en Configuración → Automatización
    - Admin ahora ve "Configuración" en el sidebar
    - Fidelización ahora envía realmente por WhatsApp

## Backlog Priorizado
### P1
- Crear templates en Meta Business Manager (tarea del usuario)
- Configurar flujos IA para 3 productos restantes (requiere input del usuario)
- Dividir componentes grandes del frontend
- Refactorizar server.py (~4400 líneas) en routers modulares

### P2
- Type hints en backend Python
- Reportes automáticos por email semanales

## Credenciales
- Admin: admin@fakulti.com / Admin123!
- Developer: aicreator@emprenovus.com / Jlsb*1082
