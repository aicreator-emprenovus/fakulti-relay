# Faculty CRM + Embudo Inteligente + Juegos - PRD

## Problema Original
CRM completo para Fakulti Laboratorios (Faculty) con embudo inteligente de 6 etapas, 3 juegos interactivos, chat IA, cotizaciones PDF, fidelización, carga/descarga masiva Excel.

## Arquitectura
- **Backend**: FastAPI + MongoDB (Motor async) + Emergent Integrations (GPT-5.2)
- **Frontend**: React + Tailwind CSS + Shadcn UI + Recharts
- **Auth**: JWT con bcrypt
- **IA**: OpenAI GPT-5.2 via Emergent Universal Key

## User Personas
1. **Admin CRM**: Gestiona leads, configura juegos/fidelización, genera cotizaciones
2. **Cliente/Lead**: Interactúa con juegos vía QR, recibe seguimiento postventa
3. **Agente Ventas**: Usa chat IA para atender leads, genera cotizaciones

## Implementado (2026-03-03)
- ✅ Login JWT (admin@faculty.com / admin123)
- ✅ Dashboard con métricas (leads, ventas, conversión, embudo, fuentes)
- ✅ CRUD Leads con embudo de 6 etapas (Nuevo→Interesado→Caliente→Cliente Nuevo→Cliente Activo→Frío)
- ✅ 3 Juegos (Ruleta, Caja Misteriosa, Botón de Suerte) con páginas públicas QR
- ✅ Chat IA con GPT-5.2 (asesor virtual Faculty)
- ✅ Cotizaciones con PDF descargable
- ✅ Fidelización configurable (hasta 24 mensajes)
- ✅ Carga masiva Excel (.xlsx) con detección duplicados
- ✅ Descarga Excel por etapa/producto/fuente
- ✅ Productos CRUD (Bombro $55.95, Gomitas $13.25, CBD Colágeno $52.36, Pitch Up $21.84)
- ✅ Derivación a agente humano
- ✅ Datos semilla (6 leads, 4 productos, 3 juegos)

## Backlog Priorizado
### P0
- Integración WhatsApp real (Twilio/WhatsApp Business API)
- Notificaciones en tiempo real (WebSocket)

### P1
- Automatización de mensajes de fidelización (cron jobs)
- Recordatorios de recompra automáticos (25-30 días)
- QR code generator integrado

### P2
- Reportes avanzados con exportación
- Campañas temporales configurables
- Multi-usuario con roles
- Flujo Fibeca dedicado con tracking
