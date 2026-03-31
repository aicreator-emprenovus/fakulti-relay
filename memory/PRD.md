# Fakulti CRM - PRD

## Problema Original
Plataforma CRM completa con automatización de ventas por WhatsApp para la marca "Fakulti". Incluye tracking de leads, bots de IA por producto, campañas masivas, gamificación y reportes.

## Stack Técnico
- **Frontend**: React, Tailwind, Shadcn UI
- **Backend**: FastAPI, MongoDB (Motor)
- **AI**: GPT-5.2 via emergentintegrations (v0.1.1)
- **WhatsApp**: Meta Cloud API v25.0

## Roles del Sistema
1. **Desarrollador** (dev@fakulti.com): Acceso a Configuración + Centro de Entrenamiento. Puede resetear contraseñas de Admin.
2. **Admin** (admin@fakulti.com): Dashboard, Chat, Leads, Asesores, Campañas, QR, Juegos, Fidelización, Productos y Bots. Puede resetear contraseñas de Asesores. NO tiene acceso a Configuración ni Centro de Entrenamiento.
3. **Asesor**: Dashboard, Chat, Leads (solo asignados).

## Centro de Entrenamiento del Bot (Developer)
- **Personalidad Global**: Nombre del bot, marca, tono, estilo de saludo/despedida, frases prohibidas, instrucciones adicionales, max emojis, max líneas, idioma
- **Base de Conocimiento / FAQ**: Preguntas y respuestas que el bot consulta automáticamente
- **Consola de Pruebas**: Chat simulado para probar el bot con la configuración actual
- **Gestión de Accesos**: Ver solicitudes de reset de contraseña, resetear passwords de admins

## Flujo "Olvidé mi Contraseña"
- Admin → "La solicitud fue enviada al desarrollador del sistema" → Developer resuelve
- Asesor → "La solicitud fue enviada al Administrador del sistema" → Admin resuelve
- Admin también puede resetear contraseñas de asesores directamente desde la página Asesores

## Flujo WhatsApp
Bidireccional, completamente funcional con memoria anti-amnesia, recordatorios inteligentes por etapa, detección de hot leads con campana titilante.

## Credenciales de Prueba
- Developer: dev@fakulti.com / dev2026
- Admin: admin@fakulti.com / admin123
- Asesor: carlos@fakulti.com / advisor123
