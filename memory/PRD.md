# Fakulti CRM - PRD

## Problema Original
Plataforma CRM completa con automatización de ventas por WhatsApp para la marca "Fakulti".

## Arquitectura
- Frontend: React + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB (Motor)
- AI: GPT-5.2 via emergentintegrations
- External API: Meta WhatsApp Cloud API v25.0

## Funcionalidades Implementadas
1. WhatsApp Bot bidireccional con Meta Cloud API v25.0
2. AI Bot (GPT-5.2) con historial de conversación y Anti-Amnesia
3. Smart Reminders contextuales por etapa de lead
4. Alerta visual de Lead Caliente
5. Roles: Admin, Asesor, Desarrollador
6. Centro de Entrenamiento IA + Consola de Pruebas aislada
7. Panel de Alertas + Contraseñas provisionales
8. Scheduler automático de recordatorios (cada 30 min)
9. Soporte de Message Templates de Meta
10. Export/Import/Delete de reglas de automatización (Excel)
11. Alerta inmediata cuando cliente solicita asesor
12. Flujo completo de contraseñas provisionales con seguridad alta

## Backlog
### P1
- Crear templates en Meta Business Manager
- Configurar flujos IA para 3 productos restantes
- Refactorizar server.py en routers modulares

### P2
- Type hints en backend
- Reportes automáticos por email

## Credenciales
- Admin: admin@fakulti.com / Admin123!
- Developer: aicreator@emprenovus.com / Jlsb*1082
