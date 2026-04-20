"""Audit log helper — writes user activity to `audit_logs` collection."""
import logging
import re
from datetime import datetime, timezone
from typing import Optional
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
    ("POST", r"^/api/automation-rules", "Creación de regla de automatización"),
    ("PUT", r"^/api/automation-rules/[^/]+", "Actualización de regla de automatización"),
    ("DELETE", r"^/api/automation-rules/[^/]+", "Eliminación de regla de automatización"),
    ("POST", r"^/api/config/whatsapp", "Actualización de configuración WhatsApp"),
    ("POST", r"^/api/quotations$", "Creación de cotización"),
    ("DELETE", r"^/api/quotations/[^/]+$", "Eliminación de cotización"),
    ("POST", r"^/api/loyalty", "Acción de fidelización"),
]


def friendly_label(method: str, path: str) -> str:
    for m, pattern, label in _LABELS:
        if m == method and re.match(pattern, path):
            return label
    return f"{method} {path}"


async def log_event(
    action: str,
    user: Optional[dict] = None,
    details: Optional[str] = None,
    ip: str = "",
    path: str = "",
    method: str = "",
    status: int = 0,
    user_agent: str = "",
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
        }
        await db.audit_logs.insert_one(doc)
    except Exception as e:
        logger.warning(f"Audit log insert failed: {e}")
