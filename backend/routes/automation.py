from fastapi import APIRouter, HTTPException, Depends
import uuid
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from database import db
from auth import get_current_user
from models import AutomationRuleCreate
from whatsapp_utils import get_whatsapp_config, send_whatsapp_message, send_whatsapp_template

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/automation/rules")
async def get_automation_rules(user=Depends(get_current_user)):
    rules = await db.automation_rules.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return rules


@router.post("/automation/rules")
async def create_automation_rule(req: AutomationRuleCreate, user=Depends(get_current_user)):
    count = await db.automation_rules.count_documents({})
    doc = {"id": str(uuid.uuid4()), **req.model_dump(), "order": count + 1, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.automation_rules.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/automation/rules/{rule_id}")
async def update_automation_rule(rule_id: str, req: AutomationRuleCreate, user=Depends(get_current_user)):
    await db.automation_rules.update_one({"id": rule_id}, {"$set": req.model_dump()})
    rule = await db.automation_rules.find_one({"id": rule_id}, {"_id": 0})
    return rule


@router.patch("/automation/rules/{rule_id}/toggle")
async def toggle_automation_rule(rule_id: str, user=Depends(get_current_user)):
    rule = await db.automation_rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    new_active = not rule.get("active", True)
    await db.automation_rules.update_one({"id": rule_id}, {"$set": {"active": new_active}})
    return {"active": new_active}


@router.delete("/automation/rules/all")
async def delete_all_automation_rules(user=Depends(get_current_user)):
    if user.get("role") not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Sin permisos")
    result = await db.automation_rules.delete_many({})
    return {"message": f"{result.deleted_count} reglas eliminadas", "deleted": result.deleted_count}


@router.delete("/automation/rules/{rule_id}")
async def delete_automation_rule(rule_id: str, user=Depends(get_current_user)):
    await db.automation_rules.delete_one({"id": rule_id})
    return {"message": "Regla eliminada"}


@router.get("/automation/rules/export")
async def export_automation_rules(user=Depends(get_current_user)):
    rules = await db.automation_rules.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return rules


@router.post("/automation/rules/import")
async def import_automation_rules(body: dict, user=Depends(get_current_user)):
    rules_data = body.get("rules", [])
    if not rules_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron reglas")
    imported = 0
    for r in rules_data:
        doc = {
            "id": str(uuid.uuid4()),
            "name": r.get("name", "Regla importada"),
            "trigger_type": r.get("trigger_type", "sin_respuesta"),
            "trigger_value": str(r.get("trigger_value", "")),
            "action_type": r.get("action_type", "enviar_mensaje"),
            "action_value": r.get("action_value", ""),
            "description": r.get("description", ""),
            "active": r.get("active", True) if isinstance(r.get("active"), bool) else str(r.get("active", "true")).lower() in ("true", "1", "si", "si"),
            "wa_template_name": r.get("wa_template_name", ""),
            "wa_template_language": r.get("wa_template_language", "es"),
            "order": imported + 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.automation_rules.insert_one(doc)
        imported += 1
    return {"message": f"{imported} reglas importadas exitosamente", "imported": imported}


@router.get("/automation/log")
async def get_automation_log(limit: int = 50, user=Depends(get_current_user)):
    logs = await db.automation_log.find({}, {"_id": 0}).sort("sent_at", -1).to_list(limit)
    return logs


@router.post("/automation/run-now")
async def run_automation_now(user=Depends(get_current_user)):
    if user.get("role") not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Sin permisos")

    wa_config = await get_whatsapp_config()
    wa_ready = wa_config and wa_config.get("phone_number_id") and wa_config.get("access_token")
    if not wa_ready:
        raise HTTPException(status_code=400, detail="WhatsApp no esta configurado")

    rules = await db.automation_rules.find({"active": True, "trigger_type": "sin_respuesta"}, {"_id": 0}).to_list(50)
    if not rules:
        return {"message": "No hay reglas activas de tipo 'sin_respuesta'", "sent": 0}

    now = datetime.now(timezone.utc)
    total_sent = 0
    total_failed = 0
    total_actions = 0
    details = []

    for rule in rules:
        try:
            hours = int(rule.get("trigger_value", "24"))
            cutoff = (now - timedelta(hours=hours)).isoformat()
            max_hours = hours * 2
            upper_cutoff = (now - timedelta(hours=max_hours)).isoformat() if max_hours < 200 else None

            query = {
                "last_interaction": {"$lte": cutoff},
                "whatsapp": {"$ne": ""},
                "funnel_stage": {"$nin": ["perdido", "cliente_activo"]},
            }
            if upper_cutoff:
                query["last_interaction"]["$gte"] = upper_cutoff

            leads = await db.leads.find(query, {"_id": 0, "id": 1, "name": 1, "whatsapp": 1, "funnel_stage": 1}).to_list(50)

            for lead in leads:
                lead_id = lead["id"]
                phone = lead.get("whatsapp", "")
                if not phone:
                    continue

                already_sent = await db.automation_log.find_one({
                    "lead_id": lead_id, "rule_id": rule["id"],
                    "sent_at": {"$gte": cutoff}
                }, {"_id": 0})
                if already_sent:
                    continue

                action_type = rule.get("action_type", "enviar_mensaje")

                if action_type == "enviar_mensaje":
                    msg = rule.get("action_value", "")
                    if not msg:
                        continue
                    lead_name = lead.get("name", "").split()[0] if lead.get("name") else ""
                    if lead_name:
                        msg = msg.replace("{nombre}", lead_name)

                    wa_template = rule.get("wa_template_name", "")
                    wa_sent = False
                    if wa_template:
                        wa_sent = await send_whatsapp_template(phone, wa_template, rule.get("wa_template_language", "es"), [lead_name or "cliente"])
                    else:
                        wa_sent = await send_whatsapp_message(phone, msg)

                    if wa_sent:
                        session_id = f"wa_{phone}"
                        await db.chat_messages.insert_one({
                            "id": str(uuid.uuid4()), "session_id": session_id,
                            "lead_id": lead_id, "role": "assistant",
                            "content": msg, "timestamp": now.isoformat(),
                            "source": "auto_reminder"
                        })
                        total_sent += 1
                        details.append(f"{lead.get('name', phone)}: {rule['name']} - Enviado")
                    else:
                        total_failed += 1
                        details.append(f"{lead.get('name', phone)}: {rule['name']} - Fallo (24h window / template)")

                elif action_type == "cambiar_etapa":
                    new_stage = rule.get("action_value", "")
                    if new_stage:
                        await db.leads.update_one({"id": lead_id}, {"$set": {"funnel_stage": new_stage}})
                        total_actions += 1
                        details.append(f"{lead.get('name', phone)}: {rule['name']} - Etapa -> {new_stage}")

                await db.automation_log.insert_one({
                    "lead_id": lead_id, "rule_id": rule["id"],
                    "rule_name": rule.get("name", ""),
                    "action_type": action_type,
                    "sent_at": now.isoformat(), "success": True
                })

        except Exception as e:
            details.append(f"Error en regla '{rule.get('name', '?')}': {str(e)[:100]}")

    return {
        "message": f"Automatizacion ejecutada: {total_sent} enviados, {total_failed} fallidos, {total_actions} cambios de etapa",
        "sent": total_sent, "failed": total_failed, "actions": total_actions,
        "details": details[:20]
    }


async def process_automation_rules_background():
    """Background task: processes sin_respuesta automation rules every 30 minutes."""
    while True:
        try:
            await asyncio.sleep(1800)

            wa_config = await get_whatsapp_config()
            wa_ready = wa_config and wa_config.get("phone_number_id") and wa_config.get("access_token")
            if not wa_ready:
                logger.debug("Automation scheduler: WhatsApp not configured, skipping")
                continue

            rules = await db.automation_rules.find({"active": True, "trigger_type": "sin_respuesta"}, {"_id": 0}).to_list(50)
            if not rules:
                continue

            now = datetime.now(timezone.utc)
            total_sent = 0
            total_actions = 0

            for rule in rules:
                try:
                    hours = int(rule.get("trigger_value", "24"))
                    cutoff = (now - timedelta(hours=hours)).isoformat()
                    max_hours = hours * 2
                    upper_cutoff = (now - timedelta(hours=max_hours)).isoformat() if max_hours < 200 else None

                    query = {
                        "last_interaction": {"$lte": cutoff},
                        "whatsapp": {"$ne": ""},
                        "funnel_stage": {"$nin": ["perdido", "cliente_activo"]},
                    }
                    if upper_cutoff:
                        query["last_interaction"]["$gte"] = upper_cutoff

                    leads = await db.leads.find(query, {"_id": 0, "id": 1, "name": 1, "whatsapp": 1, "funnel_stage": 1, "product_interest": 1, "last_interaction": 1}).to_list(50)

                    for lead in leads:
                        lead_id = lead["id"]
                        phone = lead.get("whatsapp", "")
                        if not phone:
                            continue

                        already_sent = await db.automation_log.find_one({
                            "lead_id": lead_id, "rule_id": rule["id"],
                            "sent_at": {"$gte": cutoff}
                        }, {"_id": 0})
                        if already_sent:
                            continue

                        action_type = rule.get("action_type", "enviar_mensaje")

                        if action_type == "enviar_mensaje":
                            msg = rule.get("action_value", "")
                            if not msg:
                                continue
                            lead_name = lead.get("name", "").split()[0] if lead.get("name") else ""
                            if lead_name:
                                msg = msg.replace("{nombre}", lead_name)
                            wa_template = rule.get("wa_template_name", "")
                            wa_sent = False
                            if wa_template:
                                wa_sent = await send_whatsapp_template(phone, wa_template, rule.get("wa_template_language", "es"), [lead_name or "cliente"])
                            else:
                                wa_sent = await send_whatsapp_message(phone, msg)
                            if wa_sent:
                                session_id = f"wa_{phone}"
                                await db.chat_messages.insert_one({
                                    "id": str(uuid.uuid4()), "session_id": session_id,
                                    "lead_id": lead_id, "role": "assistant",
                                    "content": msg, "timestamp": now.isoformat(),
                                    "source": "auto_reminder"
                                })
                                total_sent += 1
                                logger.info(f"Auto-reminder sent to {lead.get('name', phone)} ({phone}) - Rule: {rule['name']}")
                            else:
                                logger.warning(f"Auto-reminder failed for {phone} - Rule: {rule['name']}")

                        elif action_type == "cambiar_etapa":
                            new_stage = rule.get("action_value", "")
                            if new_stage:
                                await db.leads.update_one({"id": lead_id}, {"$set": {"funnel_stage": new_stage}})
                                total_actions += 1
                                logger.info(f"Auto-stage change: {lead.get('name', phone)} -> {new_stage} - Rule: {rule['name']}")

                        await db.automation_log.insert_one({
                            "lead_id": lead_id, "rule_id": rule["id"],
                            "rule_name": rule.get("name", ""),
                            "action_type": action_type,
                            "sent_at": now.isoformat(), "success": True
                        })

                except Exception as e:
                    logger.error(f"Automation rule error ({rule.get('name', '?')}): {e}")

            if total_sent > 0 or total_actions > 0:
                logger.info(f"Automation scheduler: {total_sent} messages sent, {total_actions} stage changes")

        except Exception as e:
            logger.error(f"Automation scheduler error: {e}")
            await asyncio.sleep(60)
