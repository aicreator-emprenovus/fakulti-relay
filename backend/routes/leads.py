from fastapi import APIRouter, HTTPException, Depends, Query
import uuid
import logging
from datetime import datetime, timezone
from database import db
from auth import get_current_user
from models import LeadCreate, LeadUpdate, PurchaseAdd

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/leads")
async def get_leads(
    stage: str = None,
    source: str = None,
    search: str = None,
    assigned_advisor: str = None,
    needs_advisor: bool = None,
    user=Depends(get_current_user)
):
    query = {}
    if stage:
        query["funnel_stage"] = stage
    if source:
        query["source"] = source
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"whatsapp": {"$regex": search}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if assigned_advisor:
        query["assigned_advisor"] = assigned_advisor
    if needs_advisor:
        query["needs_advisor"] = True
        query["$or"] = [{"assigned_advisor": ""}, {"assigned_advisor": {"$exists": False}}]

    user_role = user.get("role", "admin")
    user_id = user["id"]
    if user_role == "advisor":
        query["assigned_advisor"] = user_id

    leads = await db.leads.find(query, {"_id": 0}).sort("last_interaction", -1).to_list(500)
    total = await db.leads.count_documents(query)
    return {"leads": leads, "total": total}


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str, user=Depends(get_current_user)):
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    if lead.get("assigned_advisor"):
        advisor = await db.admin_users.find_one({"id": lead["assigned_advisor"], "role": "advisor"}, {"_id": 0, "name": 1})
        lead["_advisor_name"] = advisor["name"] if advisor else ""
    return lead


@router.post("/leads")
async def create_lead(req: LeadCreate, user=Depends(get_current_user)):
    lead_doc = {
        "id": str(uuid.uuid4()),
        **req.model_dump(),
        "status": "activo",
        "game_used": None,
        "prize_obtained": None,
        "purchase_history": [],
        "coupon_used": None,
        "recompra_date": None,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.leads.insert_one(lead_doc)
    lead_doc.pop("_id", None)
    return lead_doc


@router.put("/leads/{lead_id}")
async def update_lead(lead_id: str, req: LeadUpdate, user=Depends(get_current_user)):
    update = {k: v for k, v in req.model_dump().items() if v is not None}
    update["last_interaction"] = datetime.now(timezone.utc).isoformat()
    await db.leads.update_one({"id": lead_id}, {"$set": update})
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    return lead


@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, user=Depends(get_current_user)):
    await db.leads.delete_one({"id": lead_id})
    await db.chat_messages.delete_many({"lead_id": lead_id})
    return {"message": "Lead eliminado"}


@router.post("/leads/{lead_id}/purchase")
async def add_purchase(lead_id: str, req: PurchaseAdd, user=Depends(get_current_user)):
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    purchase = {
        "id": str(uuid.uuid4()),
        "product_id": req.product_id,
        "product_name": req.product_name,
        "quantity": req.quantity,
        "price": req.price * req.quantity,
        "date": datetime.now(timezone.utc).isoformat()[:10]
    }
    new_stage = lead.get("funnel_stage", "nuevo")
    if new_stage in ("nuevo", "interesado", "en_negociacion"):
        new_stage = "cliente_nuevo"
    await db.leads.update_one(
        {"id": lead_id},
        {"$push": {"purchase_history": purchase}, "$set": {"funnel_stage": new_stage, "last_interaction": datetime.now(timezone.utc).isoformat()}}
    )

    # Auto-enroll in loyalty sequence if configured
    config = await db.system_config.find_one({"id": "auto_enroll_config"}, {"_id": 0})
    if config and config.get("enabled") and config.get("default_sequence_id"):
        target_stage = config.get("target_stage", "cliente_nuevo")
        if new_stage == target_stage:
            existing_enrollment = await db.loyalty_enrollments.find_one({"lead_id": lead_id, "sequence_id": config["default_sequence_id"]}, {"_id": 0})
            if not existing_enrollment:
                seq = await db.loyalty_sequences.find_one({"id": config["default_sequence_id"]}, {"_id": 0})
                if seq:
                    enrollment = {
                        "id": str(uuid.uuid4()),
                        "lead_id": lead_id,
                        "lead_name": lead.get("name", ""),
                        "sequence_id": seq["id"],
                        "sequence_name": seq.get("product_name", ""),
                        "current_step": 0,
                        "status": "active",
                        "enrolled_at": datetime.now(timezone.utc).isoformat(),
                        "last_message_sent": None,
                        "next_message_date": datetime.now(timezone.utc).isoformat()
                    }
                    await db.loyalty_enrollments.insert_one(enrollment)
                    logger.info(f"Auto-enrolled lead {lead_id} in sequence {seq['id']}")

    updated_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    return updated_lead


@router.put("/leads/{lead_id}/stage")
async def update_lead_stage(lead_id: str, stage: str = Query(...)):
    await db.leads.update_one({"id": lead_id}, {"$set": {"funnel_stage": stage, "last_interaction": datetime.now(timezone.utc).isoformat()}})
    return {"message": f"Stage updated to {stage}"}


@router.put("/leads/{lead_id}/assign")
async def assign_lead_to_advisor(lead_id: str, body: dict, user=Depends(get_current_user)):
    advisor_id = body.get("advisor_id", "")
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    if advisor_id:
        advisor = await db.admin_users.find_one({"id": advisor_id, "role": "advisor"}, {"_id": 0})
        if not advisor:
            raise HTTPException(status_code=404, detail="Asesor no encontrado")
    await db.leads.update_one({"id": lead_id}, {"$set": {"assigned_advisor": advisor_id, "needs_advisor": False, "last_interaction": datetime.now(timezone.utc).isoformat()}})
    updated = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    return updated


@router.put("/leads/{lead_id}/pause-bot")
async def pause_bot_for_lead(lead_id: str, user=Depends(get_current_user)):
    result = await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"bot_paused": True, "bot_paused_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    logger.info(f"Bot paused for lead {lead_id} - human agent taking over")
    return {"message": "Bot pausado. El agente humano tiene el control."}


@router.put("/leads/{lead_id}/resume-bot")
async def resume_bot_for_lead(lead_id: str, user=Depends(get_current_user)):
    result = await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"bot_paused": False}, "$unset": {"bot_paused_at": ""}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    logger.info(f"Bot resumed for lead {lead_id}")
    return {"message": "Bot reactivado para este lead."}


@router.post("/leads/{lead_id}/derive-human")
async def derive_to_human(lead_id: str, reason: str = Query("general"), user=Depends(get_current_user)):
    await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"status": "gestion_humana", "notes": f"Derivado a agente humano: {reason}", "last_interaction": datetime.now(timezone.utc).isoformat()}}
    )
    notification = {
        "id": str(uuid.uuid4()),
        "type": "derivacion_humana",
        "lead_id": lead_id,
        "reason": reason,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    return {"message": "Lead derivado a agente humano"}


@router.post("/leads/{lead_id}/reset-bot-context")
async def reset_bot_context(lead_id: str, user=Depends(get_current_user)):
    """Resetea el contexto del bot para este lead: el historial previo sigue visible en el CRM
    pero el bot lo ignora a partir de ahora. También limpia campos acumulados (cantidad, dirección,
    CI/RUC, producto de interés) que pudieron contaminarse con pruebas anteriores.
    Mantiene intactos: nombre, teléfono, email, canal, stage."""
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    reset_at = datetime.now(timezone.utc).isoformat()
    await db.leads.update_one(
        {"id": lead_id},
        {
            "$set": {"bot_context_reset_at": reset_at, "last_interaction": reset_at},
            "$unset": {
                "quantity_requested": "",
                "address": "",
                "ci_ruc": "",
                "product_interest": ""
            }
        }
    )
    # Cancel any pending handover alerts so the bot starts truly fresh
    await db.handover_alerts.update_many(
        {"lead_id": lead_id, "status": "pending"},
        {"$set": {"status": "cancelled", "resolved_at": reset_at}}
    )
    logger.info(f"Bot context reset for lead {lead_id} at {reset_at}")
    return {"message": "Contexto del bot reseteado. El bot empieza fresco en la próxima interacción.", "reset_at": reset_at}
