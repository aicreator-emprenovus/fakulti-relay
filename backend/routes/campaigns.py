from fastapi import APIRouter, HTTPException, Depends, Query
import uuid
import os
import logging
import random
from datetime import datetime, timezone, timedelta
from database import db
from auth import get_current_user
from utils import normalize_phone_ec
from models import QRCampaignCreate, CampaignCreate, ReminderCreate
from whatsapp_utils import (
    get_whatsapp_config, send_whatsapp_message,
    send_whatsapp_image, send_whatsapp_template, WHATSAPP_API_URL
)
import httpx

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

REMINDER_TEMPLATES_BY_STAGE = {
    "cliente_nuevo": [
        "Hola {nombre} Esperamos que estes disfrutando tu producto. Si necesitas algo adicional o tienes alguna consulta, estamos para ayudarte.",
        "Hola {nombre}, queremos saber como te fue con tu pedido. Necesitas algo mas? Estamos a tu disposicion.",
    ],
    "cliente_activo": [
        "Hola {nombre} Como te ha ido con tu producto? Si necesitas asesoria o reposicion, aqui estamos para ti.",
        "Hola {nombre}, esperamos que todo vaya bien. Si necesitas algo mas, no dudes en escribirnos.",
    ],
    "en_negociacion": [
        "Hola {nombre} Vimos que estabas interesado en {producto}. Tienes alguna duda que podamos resolver para avanzar con tu pedido?",
        "Hola {nombre}, solo queriamos saber si pudiste decidirte por {producto}. Estamos listos para ayudarte a concretar tu compra.",
    ],
    "interesado": [
        "Hola {nombre} Notamos que te interesaba {producto}. Te gustaria mas informacion o tienes alguna pregunta?",
        "Hola {nombre}, seguimos con disponibilidad de {producto}. Quieres que te cuente mas sobre sus beneficios?",
    ],
    "nuevo": [
        "Hola {nombre} Soy el asesor virtual de Fakulti. En que puedo ayudarte hoy?",
        "Hola {nombre}, hay algun producto de Fakulti que te interese? Con gusto te asesoro.",
    ],
}


def _build_smart_reminder_message(lead: dict, custom_template: str = "") -> str:
    name = lead.get("name", "").split()[0] if lead.get("name") else ""
    stage = lead.get("funnel_stage", "nuevo")
    product = lead.get("product_interest", "nuestros productos")
    if custom_template:
        return custom_template.replace("{nombre}", name).replace("{producto}", product)
    templates = REMINDER_TEMPLATES_BY_STAGE.get(stage, REMINDER_TEMPLATES_BY_STAGE["nuevo"])
    template = random.choice(templates)
    return template.replace("{nombre}", name).replace("{producto}", product)


# ========== QR CAMPAIGNS ==========

@router.get("/qr-campaigns")
async def get_qr_campaigns(user=Depends(get_current_user)):
    campaigns = await db.qr_campaigns.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    for c in campaigns:
        c["scan_count"] = c.get("scan_count", 0)
    return campaigns


@router.post("/qr-campaigns")
async def create_qr_campaign(req: QRCampaignCreate, user=Depends(get_current_user)):
    doc = {
        "id": str(uuid.uuid4()),
        **req.model_dump(),
        "scan_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.qr_campaigns.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/qr-campaigns/{campaign_id}")
async def update_qr_campaign(campaign_id: str, req: QRCampaignCreate, user=Depends(get_current_user)):
    await db.qr_campaigns.update_one({"id": campaign_id}, {"$set": req.model_dump()})
    campaign = await db.qr_campaigns.find_one({"id": campaign_id}, {"_id": 0})
    return campaign


@router.delete("/qr-campaigns/{campaign_id}")
async def delete_qr_campaign(campaign_id: str, user=Depends(get_current_user)):
    await db.qr_campaigns.delete_one({"id": campaign_id})
    return {"message": "Campana QR eliminada"}


@router.get("/qr-campaigns/{campaign_id}/qrcode")
async def generate_qr_code(campaign_id: str):
    campaign = await db.qr_campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campana no encontrada")

    config = await get_whatsapp_config()
    phone = config.get("phone_number_id", "")

    if phone:
        try:
            url = f"{WHATSAPP_API_URL}/{phone}"
            headers = {"Authorization": f"Bearer {config['access_token']}"}
            async with httpx.AsyncClient() as c:
                resp = await c.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    display_phone = data.get("display_phone_number", "")
                    if display_phone:
                        phone = display_phone.replace("+", "").replace(" ", "")
        except Exception:
            pass

    if not phone:
        phone = "593XXXXXXXXX"

    msg = campaign.get("initial_message", "Hola")
    wa_link = f"https://wa.me/{phone}?text={msg.replace(' ', '%20')}"

    return {
        "qr_data": wa_link,
        "wa_link": wa_link,
        "campaign": campaign,
        "phone": phone
    }


@router.get("/qr-campaigns/{campaign_id}/link")
async def get_qr_link(campaign_id: str, user=Depends(get_current_user)):
    campaign = await db.qr_campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campana no encontrada")
    config = await get_whatsapp_config()
    phone = config.get("phone_number_id", "")
    if phone:
        try:
            url = f"{WHATSAPP_API_URL}/{phone}"
            headers = {"Authorization": f"Bearer {config['access_token']}"}
            async with httpx.AsyncClient() as c:
                resp = await c.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    display_phone = data.get("display_phone_number", "")
                    if display_phone:
                        phone = display_phone.replace("+", "").replace(" ", "")
        except Exception:
            pass
    if not phone:
        phone = "593XXXXXXXXX"
    msg = campaign.get("initial_message", "Hola")
    wa_link = f"https://wa.me/{phone}?text={msg.replace(' ', '%20')}"
    return {"link": wa_link, "campaign": campaign}


# ========== PROMOTIONAL CAMPAIGNS ==========

@router.get("/campaigns")
async def get_campaigns(user=Depends(get_current_user)):
    campaigns = await db.campaigns.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return campaigns


@router.post("/campaigns")
async def create_campaign(req: CampaignCreate, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    query = {}
    if req.target_stage:
        query["funnel_stage"] = req.target_stage
    if req.target_product:
        query["product_interest"] = {"$regex": req.target_product, "$options": "i"}
    if req.target_channel:
        query["channel"] = req.target_channel
    if req.target_season:
        query["season"] = req.target_season
    target_count = await db.leads.count_documents(query)
    campaign = {
        "id": str(uuid.uuid4()),
        **req.model_dump(),
        "target_count": target_count,
        "sent_count": 0,
        "failed_count": 0,
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.campaigns.insert_one(campaign)
    campaign.pop("_id", None)
    return campaign


@router.put("/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, req: CampaignCreate, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    update = {k: v for k, v in req.model_dump().items() if v is not None}
    query = {}
    if req.target_stage:
        query["funnel_stage"] = req.target_stage
    if req.target_product:
        query["product_interest"] = {"$regex": req.target_product, "$options": "i"}
    if req.target_channel:
        query["channel"] = req.target_channel
    update["target_count"] = await db.leads.count_documents(query)
    await db.campaigns.update_one({"id": campaign_id}, {"$set": update})
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    return campaign


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    await db.campaigns.delete_one({"id": campaign_id})
    return {"message": "Campana eliminada"}


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(campaign_id: str, body: dict = {}, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campana no encontrada")

    wa_config = await get_whatsapp_config()
    if not wa_config or not wa_config.get("phone_number_id") or not wa_config.get("access_token"):
        raise HTTPException(status_code=400, detail="WhatsApp no esta configurado. Ve a Configuracion y agrega tu Phone Number ID y Access Token de Meta.")

    batch_size = body.get("batch_size", 50)
    query = {}
    if campaign.get("target_stage"):
        query["funnel_stage"] = campaign["target_stage"]
    if campaign.get("target_product"):
        query["product_interest"] = {"$regex": campaign["target_product"], "$options": "i"}
    if campaign.get("target_channel"):
        query["channel"] = campaign["target_channel"]

    leads = await db.leads.find(query, {"_id": 0, "id": 1, "name": 1, "whatsapp": 1}).to_list(500)

    if not leads:
        raise HTTPException(status_code=400, detail="No hay leads que coincidan con los filtros de esta campana")

    await db.campaigns.update_one({"id": campaign_id}, {"$set": {"target_count": len(leads)}})

    sent = 0
    failed = 0
    errors = []
    now_iso = datetime.now(timezone.utc).isoformat()

    public_url = os.environ.get("PUBLIC_URL", "").rstrip("/")
    if not public_url:
        public_url = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

    for lead in leads[:batch_size]:
        phone = lead.get("whatsapp", "")
        if not phone:
            failed += 1
            errors.append(f"{lead.get('name', 'Sin nombre')}: sin numero de WhatsApp")
            continue

        try:
            msg = campaign["message_template"].replace("{nombre}", lead.get("name", "").split()[0] if lead.get("name") else "")
            lead_id = lead["id"]
            image_url = campaign.get("image_url", "")
            wa_template_name = campaign.get("wa_template_name", "")
            wa_template_lang = campaign.get("wa_template_language", "es")

            full_image_url = ""
            if image_url:
                full_image_url = image_url
                if image_url.startswith("/api/") or image_url.startswith("/"):
                    full_image_url = f"{public_url}{image_url}"

            wa_success = False

            if wa_template_name:
                lead_name = lead.get("name", "").split()[0] if lead.get("name") else "cliente"
                params = [lead_name]
                wa_success = await send_whatsapp_template(
                    phone, wa_template_name, wa_template_lang, params,
                    image_url=full_image_url if full_image_url else None
                )
                if not wa_success:
                    errors.append(f"{lead.get('name', phone)}: Template '{wa_template_name}' fallo. Verifica que este aprobado en Meta.")
            else:
                if full_image_url:
                    wa_success = await send_whatsapp_image(phone, full_image_url, msg)
                else:
                    wa_success = await send_whatsapp_message(phone, msg)
                if not wa_success:
                    errors.append(f"{lead.get('name', phone)}: Fallo. Si el lead no escribio en 24h, usa un Template de Meta.")

            if not wa_success:
                failed += 1
                continue

            wa_session_id = f"wa_{phone}"
            meta = await db.chat_sessions_meta.find_one({"session_id": wa_session_id}, {"_id": 0})
            if not meta:
                meta = await db.chat_sessions_meta.find_one({"lead_id": lead_id, "source": "whatsapp"}, {"_id": 0})
            if not meta:
                meta = await db.chat_sessions_meta.find_one({"lead_id": lead_id}, {"_id": 0})
            if not meta:
                session_id = wa_session_id
                await db.chat_sessions_meta.insert_one({
                    "session_id": session_id, "lead_id": lead_id,
                    "lead_name": lead.get("name", ""), "lead_phone": phone, "source": "whatsapp"
                })
            else:
                session_id = meta["session_id"]

            content = msg
            if image_url:
                content += f"\n[Imagen: {image_url}]"
            chat_msg = {
                "id": str(uuid.uuid4()), "session_id": session_id,
                "role": "assistant", "content": content,
                "timestamp": now_iso, "source": "campaign"
            }
            await db.chat_messages.insert_one(chat_msg)
            await db.leads.update_one({"id": lead_id}, {"$set": {"last_interaction": now_iso}})
            sent += 1
        except Exception as e:
            logger.error(f"Campaign send error for lead {lead.get('id')}: {e}")
            failed += 1
            errors.append(f"{lead.get('name', phone)}: {str(e)[:80]}")

    status = "sent" if sent > 0 else "failed"
    await db.campaigns.update_one({"id": campaign_id}, {
        "$set": {"status": status, "sent_count": campaign.get("sent_count", 0) + sent, "failed_count": campaign.get("failed_count", 0) + failed,
                 "last_sent_at": now_iso}
    })

    result = {"message": f"Campana: {sent} enviados, {failed} fallidos de {len(leads[:batch_size])} leads", "sent": sent, "failed": failed}
    if errors:
        result["errors"] = errors[:10]
    return result


# ========== SMART REMINDERS ==========

@router.get("/reminders")
async def get_reminders(user=Depends(get_current_user)):
    reminders = await db.reminders.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return reminders


@router.post("/reminders")
async def create_reminder(req: ReminderCreate, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    reminder = {
        "id": str(uuid.uuid4()),
        **req.model_dump(),
        "last_run": None,
        "total_sent": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reminders.insert_one(reminder)
    reminder.pop("_id", None)
    return reminder


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    await db.reminders.delete_one({"id": reminder_id})
    return {"message": "Recordatorio eliminado"}


@router.post("/reminders/{reminder_id}/execute")
async def execute_reminder(reminder_id: str, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    reminder = await db.reminders.find_one({"id": reminder_id}, {"_id": 0})
    if not reminder:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

    cutoff = (datetime.now(timezone.utc) - timedelta(days=reminder.get("days_since_last_interaction", 7))).isoformat()
    query = {"last_interaction": {"$lte": cutoff}, "whatsapp": {"$ne": ""}}
    if reminder.get("target_stage"):
        query["funnel_stage"] = reminder["target_stage"]
    if reminder.get("target_product"):
        query["product_interest"] = {"$regex": reminder["target_product"], "$options": "i"}

    batch = reminder.get("batch_size", 10)
    leads = await db.leads.find(query, {"_id": 0, "id": 1, "name": 1, "whatsapp": 1, "funnel_stage": 1, "product_interest": 1}).limit(batch).to_list(batch)

    wa_config = await get_whatsapp_config()
    if not wa_config or not wa_config.get("phone_number_id") or not wa_config.get("access_token"):
        raise HTTPException(status_code=400, detail="WhatsApp no esta configurado. Ve a Configuracion y agrega tus credenciales de Meta.")

    sent = 0
    failed = 0
    errors = []
    wa_template_name = reminder.get("wa_template_name", "")
    wa_template_lang = reminder.get("wa_template_language", "es")

    for lead in leads:
        phone = lead.get("whatsapp", "")
        if not phone:
            failed += 1
            errors.append(f"{lead.get('name', 'Sin nombre')}: sin numero de WhatsApp")
            continue
        try:
            msg = _build_smart_reminder_message(lead, reminder.get("message_template", ""))
            wa_success = False

            if wa_template_name:
                lead_name = lead.get("name", "cliente").split()[0] if lead.get("name") else "cliente"
                wa_success = await send_whatsapp_template(phone, wa_template_name, wa_template_lang, [lead_name])
                if not wa_success:
                    errors.append(f"{lead.get('name', phone)}: Template '{wa_template_name}' fallo")
            else:
                wa_success = await send_whatsapp_message(phone, msg)
                if not wa_success:
                    errors.append(f"{lead.get('name', phone)}: Fallo. El lead no escribio en 24h, necesitas un Template de Meta.")

            if not wa_success:
                failed += 1
                continue

            session_id = f"wa_{phone}"
            now = datetime.now(timezone.utc).isoformat()
            await db.chat_messages.insert_one({
                "id": str(uuid.uuid4()), "session_id": session_id, "lead_id": lead.get("id"),
                "role": "assistant", "content": msg, "timestamp": now,
                "source": "reminder"
            })
            await db.chat_sessions_meta.update_one(
                {"session_id": session_id},
                {"$set": {"last_activity": now}},
                upsert=True
            )
            await db.leads.update_one({"id": lead["id"]}, {"$set": {"last_interaction": now}})
            sent += 1
        except Exception as e:
            logger.error(f"Reminder send error for {phone}: {e}")
            failed += 1
            errors.append(f"{lead.get('name', phone)}: {str(e)[:80]}")

    await db.reminders.update_one({"id": reminder_id}, {
        "$set": {"last_run": datetime.now(timezone.utc).isoformat(), "total_sent": reminder.get("total_sent", 0) + sent}
    })
    result = {"message": f"Recordatorio ejecutado: {sent} enviados, {failed} fallidos de {len(leads)} leads elegibles", "sent": sent, "failed": failed}
    if errors:
        result["errors"] = errors[:10]
    return result
