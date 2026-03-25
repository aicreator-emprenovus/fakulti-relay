# Fakulti CRM - PRD

## Problema Original
Plataforma CRM completa con automatización de ventas por WhatsApp para la marca "Fakulti". Incluye tracking de leads, bots de IA por producto, campañas masivas, gamificación y reportes.

## Stack Técnico
- **Frontend**: React, Tailwind, Shadcn UI
- **Backend**: FastAPI, MongoDB (Motor)
- **AI**: GPT-5.2 via emergentintegrations
- **Deploy**: Docker multi-stage (Node 20 + Python 3.11) para Railway

## Bloques Completados (1-13)
Todos los 13 bloques del roadmap implementados y testeados.

## Cambios Recientes (25/03/2026)
- **Chat adaptativo**: Ventana expandida en alto
- **Leads mejorados**: Etiquetas "Canal"/"Agentes", separación 25px, botones Cargar/Descargar integrados
- **Carga/Descarga eliminada**: Funcionalidad movida a Leads, tab removida
- **Fidelización simplificada**: Solo métricas
- **Asignar Asesor**: Ícono en tarjetas de leads + botón en chat WhatsApp
- **Depuración de datos**: Normalización de teléfonos, fusión de duplicados, función `find_lead_by_phone()` para búsqueda flexible, migración automática en startup

## Tareas Pendientes
- **P1**: Deploy Railway (Dockerfile listo con Node 20)
- **P1**: Flujos de venta para 4 productos (bloqueado: scripts del usuario)
- **P2**: Refactoring backend (server.py ~3400 líneas → módulos)
- **P2**: Reportes automáticos por email

## Credenciales de Prueba
- Admin: admin@fakulti.com / admin123
