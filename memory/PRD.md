# Fakulti CRM - PRD

## Problema Original
Plataforma CRM completa con automatización de ventas por WhatsApp para la marca "Fakulti". Incluye tracking de leads, bots de IA por producto, campañas masivas, gamificación y reportes.

## Stack Técnico
- **Frontend**: React, Tailwind, Shadcn UI
- **Backend**: FastAPI, MongoDB (Motor)
- **AI**: GPT-5.2 via emergentintegrations
- **Deploy**: Docker multi-stage (Node 20 + Python 3.11) para Railway

## Bloques Completados (1-13) ✅
- Dashboard con métricas
- Gestión de leads con kanban
- WhatsApp Bot con IA
- Asesores con roles
- Campañas masivas
- QR y canales de tracking
- Gamificación
- Fidelización (métricas)
- Configuración y Productos

## Cambios Recientes (25/03/2026)
- **Chat adaptativo**: Ventana de conversaciones expandida (calc 100vh - 140px)
- **Leads mejorados**: Etiquetas "Canal" y "Agentes" en filtros, separación 80px, botones Cargar/Descargar integrados
- **Carga/Descarga eliminada**: Funcionalidad movida a Leads, tab removida del sidebar
- **Fidelización simplificada**: Solo métricas (Revenue, Retención, Recompra, Top Compradores)

## Tareas Pendientes
- **P1**: Deploy Railway (Dockerfile listo con Node 20, pendiente configurar servicio)
- **P1**: Flujos de venta para 4 productos (bloqueado: scripts del usuario)
- **P2**: Refactoring backend (server.py ~3300 líneas → módulos)
- **P2**: Reportes automáticos por email

## Credenciales de Prueba
- Admin: admin@fakulti.com / admin123
