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

## Cambios Recientes
### 26/03/2026
- **P0 FIX: Imágenes en campañas WhatsApp**: Corregida la resolución de URLs de imágenes locales. Se usa `PUBLIC_URL` env var en vez de dominio hardcodeado. `send_whatsapp_image` envía payload multimedia correcto a Meta API
- **Chat: Renderizado de imágenes inline**: ChatPage.jsx detecta `[Imagen: url]` y renderiza imagen inline
- **Vista previa WhatsApp en campañas**: CampaignsPage.jsx muestra simulación tipo WhatsApp con imagen + texto + hora antes de enviar

### 25/03/2026
- Chat adaptativo, Leads mejorados, Asignar Asesor, Normalización de teléfonos
- Campañas editables con soporte de carga de imágenes
- Notificaciones con navegación a chat, Modo Humano Avanzado para Bone Broth
- Corrección ortográfica integral

## Tareas Pendientes
- **P1**: Flujos de venta IA para 3 productos restantes (Gomitas Melatonina, Colágeno CBD, Magnesio Citrato) - bloqueado: scripts del usuario
- **P1**: Refactoring backend (server.py ~3470 líneas -> módulos routes/, models/, services/)
- **P2**: Reportes automáticos por email semanal para asesores
- **P2**: Deploy Railway (SUSPENDIDO por instrucción del usuario)

## Credenciales de Prueba
- Admin: admin@fakulti.com / admin123
