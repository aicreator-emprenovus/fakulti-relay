import logging
import httpx
from database import db
from utils import phone_to_international

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v25.0"

HANDOVER_KEYWORDS = [
    "agente", "humano", "persona real", "hablar con alguien", "asesor real",
    "no quiero bot", "operador", "representante", "persona de verdad",
    "quiero hablar con una persona", "atencion humana"
]

BOT_TRANSFER_PHRASES = [
    "transfiero con un asesor", "te transfiero", "comunico con un asesor",
    "asesor se comunicara", "asesor se comunicara", "asesor te contactara",
    "asesor te contactara", "paso con un asesor", "derivo con un asesor",
    "un asesor te atendera", "un asesor te atendera", "contactar con un asesor",
    "te paso con un humano", "te comunico con alguien",
    "aviso a un asesor", "asesor te escriba", "asesor del equipo",
    "te contactara un asesor", "te contactara un asesor",
    "asesor se pondra en contacto", "asesor se pondra en contacto",
    "conecto con un asesor", "te conecto con", "conectar con un asesor",
    "asesor humano"
]

BOT_TIMEOUT_SECONDS = 60


async def get_whatsapp_config():
    config = await db.whatsapp_config.find_one({"id": "main"}, {"_id": 0})
    return config or {
        "id": "main", "phone_number_id": "", "access_token": "",
        "verify_token": "fakulti-whatsapp-verify-token",
        "business_name": "Fakulti Laboratorios"
    }


async def send_whatsapp_message(to_phone: str, text: str):
    config = await get_whatsapp_config()
    if not config.get("phone_number_id") or not config.get("access_token"):
        logger.warning("WhatsApp not configured, skipping message send")
        return False
    url = f"{WHATSAPP_API_URL}/{config['phone_number_id']}/messages"
    headers = {"Authorization": f"Bearer {config['access_token']}", "Content-Type": "application/json"}
    international = phone_to_international(to_phone)
    payload = {
        "messaging_product": "whatsapp",
        "to": international,
        "type": "text",
        "text": {"body": text}
    }
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code in (200, 201):
                logger.info(f"WA message sent to {international}")
                return True
            logger.error(f"WA send error {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"WA send exception: {e}")
        return False


async def send_whatsapp_image(to_phone: str, image_url: str, caption: str = ""):
    config = await get_whatsapp_config()
    if not config.get("phone_number_id") or not config.get("access_token"):
        logger.warning("WhatsApp not configured, skipping image send")
        return False
    url = f"{WHATSAPP_API_URL}/{config['phone_number_id']}/messages"
    headers = {"Authorization": f"Bearer {config['access_token']}", "Content-Type": "application/json"}
    international = phone_to_international(to_phone)
    payload = {
        "messaging_product": "whatsapp",
        "to": international,
        "type": "image",
        "image": {"link": image_url}
    }
    if caption:
        payload["image"]["caption"] = caption
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code in (200, 201):
                logger.info(f"WA image sent to {international}")
                return True
            logger.error(f"WA image send error {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"WA image send exception: {e}")
        return False


async def upload_whatsapp_media(file_bytes: bytes, content_type: str, filename: str):
    """Upload media to Meta Cloud API and return media_id. Works in any environment
    because the file goes directly to Meta (no public URL required)."""
    config = await get_whatsapp_config()
    if not config.get("phone_number_id") or not config.get("access_token"):
        logger.warning("WhatsApp not configured, cannot upload media")
        return None
    url = f"{WHATSAPP_API_URL}/{config['phone_number_id']}/media"
    headers = {"Authorization": f"Bearer {config['access_token']}"}
    files = {
        "file": (filename or "file", file_bytes, content_type),
        "messaging_product": (None, "whatsapp"),
        "type": (None, content_type),
    }
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.post(url, headers=headers, files=files, timeout=60)
            if resp.status_code in (200, 201):
                data = resp.json()
                media_id = data.get("id")
                logger.info(f"WA media uploaded, id={media_id}")
                return media_id
            logger.error(f"WA media upload error {resp.status_code}: {resp.text[:300]}")
            return None
    except Exception as e:
        logger.error(f"WA media upload exception: {e}")
        return None


async def send_whatsapp_media_by_id(to_phone: str, media_type: str, media_id: str, caption: str = "", filename: str = ""):
    """Send media that was previously uploaded via upload_whatsapp_media."""
    if media_type not in ("image", "document", "audio", "video"):
        return False
    config = await get_whatsapp_config()
    if not config.get("phone_number_id") or not config.get("access_token"):
        return False
    url = f"{WHATSAPP_API_URL}/{config['phone_number_id']}/messages"
    headers = {"Authorization": f"Bearer {config['access_token']}", "Content-Type": "application/json"}
    international = phone_to_international(to_phone)
    media_obj = {"id": media_id}
    if caption and media_type in ("image", "document", "video"):
        media_obj["caption"] = caption
    if filename and media_type == "document":
        media_obj["filename"] = filename
    payload = {
        "messaging_product": "whatsapp",
        "to": international,
        "type": media_type,
        media_type: media_obj,
    }
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.post(url, json=payload, headers=headers, timeout=20)
            if resp.status_code in (200, 201):
                logger.info(f"WA {media_type} (id={media_id}) sent to {international}")
                return True, ""
            err_text = resp.text[:300]
            logger.error(f"WA {media_type} send-by-id error {resp.status_code}: {err_text}")
            return False, f"Meta {resp.status_code}: {err_text[:180]}"
    except Exception as e:
        logger.error(f"WA send-by-id exception: {e}")
        return False, str(e)


async def send_whatsapp_media(to_phone: str, media_type: str, media_url: str, caption: str = "", filename: str = ""):
    """Generic sender for image / document / audio / video via link."""
    if media_type not in ("image", "document", "audio", "video"):
        logger.error(f"Unsupported media_type: {media_type}")
        return False
    config = await get_whatsapp_config()
    if not config.get("phone_number_id") or not config.get("access_token"):
        logger.warning(f"WhatsApp not configured, skipping {media_type} send")
        return False
    url = f"{WHATSAPP_API_URL}/{config['phone_number_id']}/messages"
    headers = {"Authorization": f"Bearer {config['access_token']}", "Content-Type": "application/json"}
    international = phone_to_international(to_phone)
    media_obj = {"link": media_url}
    if caption and media_type in ("image", "document", "video"):
        media_obj["caption"] = caption
    if filename and media_type == "document":
        media_obj["filename"] = filename
    payload = {
        "messaging_product": "whatsapp",
        "to": international,
        "type": media_type,
        media_type: media_obj,
    }
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.post(url, json=payload, headers=headers, timeout=20)
            if resp.status_code in (200, 201):
                logger.info(f"WA {media_type} sent to {international}")
                return True
            logger.error(f"WA {media_type} send error {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"WA {media_type} send exception: {e}")
        return False


async def send_whatsapp_template(to_phone: str, template_name: str, language: str = "es", parameters: list = None, image_url: str = None):
    config = await get_whatsapp_config()
    if not config.get("phone_number_id") or not config.get("access_token"):
        logger.warning("WhatsApp not configured, skipping template send")
        return False
    url = f"{WHATSAPP_API_URL}/{config['phone_number_id']}/messages"
    headers = {"Authorization": f"Bearer {config['access_token']}", "Content-Type": "application/json"}
    international = phone_to_international(to_phone)
    template_obj = {
        "name": template_name,
        "language": {"code": language}
    }
    components = []
    if image_url:
        components.append({
            "type": "header",
            "parameters": [{"type": "image", "image": {"link": image_url}}]
        })
    if parameters:
        body_params = [{"type": "text", "text": str(p)} for p in parameters]
        components.append({"type": "body", "parameters": body_params})
    if components:
        template_obj["components"] = components
    payload = {
        "messaging_product": "whatsapp",
        "to": international,
        "type": "template",
        "template": template_obj
    }
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code in (200, 201):
                logger.info(f"WA template '{template_name}' sent to {international}")
                return True
            logger.error(f"WA template send error {resp.status_code}: {resp.text[:300]}")
            return False
    except Exception as e:
        logger.error(f"WA template send exception: {e}")
        return False
