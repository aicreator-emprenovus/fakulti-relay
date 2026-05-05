"""Audit log helper — writes user activity to `audit_logs` collection."""
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Tuple
from database import db

logger = logging.getLogger(__name__)

# Map (method, path_pattern) -> friendly label (in Spanish)
_LABELS = [
    ("POST", r"^/api/auth/login$", "Inicio de sesión"),
    ("POST", r"^/api/auth/register$", "Registro de usuario"),
    ("POST", r"^/api/auth/change-password$", "Cambio de contraseña"),
    ("POST", r"^/api/auth/generate-provisional-password$", "Generación de contraseña provisional"),
    ("POST", r"^/api/auth/approve-reset/", "Aprobación de reset de contraseña"),
    ("POST", r"^/api/auth/reset-password", "Reset de contraseña"),
    ("POST", r"^/api/leads$", "Creación de lead"),
    ("PUT", r"^/api/leads/[^/]+$", "Actualización de lead"),
    ("DELETE", r"^/api/leads/[^/]+$", "Eliminación de lead"),
    ("POST", r"^/api/leads/[^/]+/purchase$", "Registro de compra"),
    ("PUT", r"^/api/leads/[^/]+/stage$", "Cambio de etapa del lead"),
    ("PUT", r"^/api/leads/[^/]+/assign$", "Asignación de asesor"),
    ("PUT", r"^/api/leads/[^/]+/pause-bot$", "Pausa del bot"),
    ("PUT", r"^/api/leads/[^/]+/resume-bot$", "Reactivación del bot"),
    ("POST", r"^/api/leads/[^/]+/derive-human$", "Derivación a humano"),
    ("POST", r"^/api/leads/[^/]+/reset-bot-context$", "Reset de contexto del bot"),
    ("POST", r"^/api/chat/message$", "Respuesta en chat IA"),
    ("POST", r"^/api/chat/whatsapp-reply$", "Respuesta manual por WhatsApp"),
    ("POST", r"^/api/chat/whatsapp-reply-catalog$", "Envío de catálogo por WhatsApp"),
    ("DELETE", r"^/api/chat/sessions/[^/]+$", "Eliminación de conversación"),
    ("DELETE", r"^/api/chat/messages/[^/]+$", "Eliminación de mensaje"),
    ("PUT", r"^/api/chat/alerts/[^/]+/resolve$", "Resolución de alerta"),
    ("POST", r"^/api/campaigns$", "Creación de campaña"),
    ("PUT", r"^/api/campaigns/[^/]+$", "Actualización de campaña"),
    ("DELETE", r"^/api/campaigns/[^/]+$", "Eliminación de campaña"),
    ("POST", r"^/api/campaigns/[^/]+/send$", "Envío de campaña"),
    ("POST", r"^/api/products$", "Creación de producto"),
    ("PUT", r"^/api/products/[^/]+", "Actualización de producto"),
    ("DELETE", r"^/api/products/[^/]+$", "Eliminación de producto"),
    ("POST", r"^/api/advisors$", "Creación de asesor"),
    ("PUT", r"^/api/advisors/[^/]+$", "Actualización de asesor"),
    ("DELETE", r"^/api/advisors/[^/]+$", "Eliminación de asesor"),
    ("POST", r"^/api/admins$", "Creación de administrador"),
    ("PUT", r"^/api/admins/[^/]+$", "Actualización de administrador"),
    ("DELETE", r"^/api/admins/[^/]+$", "Eliminación de administrador"),
    ("POST", r"^/api/automation/rules", "Creación de regla de automatización"),
    ("PUT", r"^/api/automation/rules/[^/]+", "Actualización de regla de automatización"),
    ("PATCH", r"^/api/automation/rules/[^/]+", "Actualización de regla de automatización"),
    ("DELETE", r"^/api/automation/rules/[^/]+", "Eliminación de regla de automatización"),
    ("POST", r"^/api/automation/rules/[^/]+/toggle", "Activación/desactivación de regla"),
    ("PATCH", r"^/api/automation/rules/[^/]+/toggle", "Activación/desactivación de regla"),
    ("POST", r"^/api/chat/whatsapp-reply-image$", "Envío de imagen por WhatsApp"),
    ("POST", r"^/api/chat/whatsapp-reply-media$", "Envío de archivo por WhatsApp"),
    ("PUT", r"^/api/advisors/notifications/[^/]+/read$", "Notificación leída"),
    ("PUT", r"^/api/config/whatsapp$", "Actualización de configuración WhatsApp"),
    ("POST", r"^/api/config/whatsapp", "Actualización de configuración WhatsApp"),
    ("POST", r"^/api/quotations$", "Creación de cotización"),
    ("DELETE", r"^/api/quotations/[^/]+$", "Eliminación de cotización"),
    ("POST", r"^/api/loyalty", "Acción de fidelización"),
]

# (regex, collection, type_label) — used to resolve entity name from path
_ENTITY_PATTERNS = [
    (re.compile(r"^/api/leads/([0-9a-fA-F-]+)"), "leads", "lead"),
    (re.compile(r"^/api/advisors/([0-9a-fA-F-]+)"), "admin_users", "asesor"),
    (re.compile(r"^/api/admins/([0-9a-fA-F-]+)"), "admin_users", "administrador"),
    (re.compile(r"^/api/products/([0-9a-fA-F-]+)"), "products", "producto"),
    (re.compile(r"^/api/campaigns/([0-9a-fA-F-]+)"), "campaigns", "campaña"),
    (re.compile(r"^/api/automation/rules/([0-9a-fA-F-]+)"), "automation_rules", "regla"),
    (re.compile(r"^/api/quotations/([0-9a-fA-F-]+)"), "quotations", "cotización"),
]


def friendly_label(method: str, path: str) -> str:
    for m, pattern, label in _LABELS:
        if m == method and re.match(pattern, path):
            return label
    return f"{method} {path}"


async def resolve_entity(path: str) -> Tuple[str, str, str]:
    """Returns (entity_type, entity_id, entity_name) for path; empty strings if not found."""
    for pattern, collection, type_label in _ENTITY_PATTERNS:
        m = pattern.match(path)
        if m:
            entity_id = m.group(1)
            try:
                doc = await db[collection].find_one({"id": entity_id}, {"_id": 0, "name": 1, "email": 1})
                if doc:
                    name = doc.get("name") or doc.get("email") or entity_id[:8]
                    return type_label, entity_id, name
                return type_label, entity_id, ""
            except Exception:
                return type_label, entity_id, ""
    return "", "", ""


async def log_event(
    action: str,
    user: Optional[dict] = None,
    details: Optional[str] = None,
    ip: str = "",
    path: str = "",
    method: str = "",
    status: int = 0,
    user_agent: str = "",
    entity_type: str = "",
    entity_id: str = "",
    entity_name: str = "",
) -> None:
    """Persist one audit event. Never raises — audit must not break business flow."""
    try:
        doc = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user_id": (user or {}).get("id", ""),
            "user_email": (user or {}).get("email", "anónimo"),
            "user_name": (user or {}).get("name", ""),
            "user_role": (user or {}).get("role", ""),
            "path": path,
            "method": method,
            "status": status,
            "ip": ip,
            "user_agent": user_agent[:200],
            "details": (details or "")[:500],
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_name": entity_name,
        }
        await db.audit_logs.insert_one(doc)
    except Exception as e:
        logger.warning(f"Audit log insert failed: {e}")

