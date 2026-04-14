from fastapi import APIRouter, HTTPException, Depends, Query
import uuid
import logging
from datetime import datetime, timezone, timedelta
from database import db
from auth import get_current_user
from models import LoyaltySequenceCreate
from whatsapp_utils import get_whatsapp_config, send_whatsapp_message, send_whatsapp_template

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/loyalty/sequences")
async def get_loyalty_sequences(user=Depends(get_current_user)):
    sequences = await db.loyalty_sequences.find({}, {"_id": 0}).to_list(100)
    return sequences


@router.post("/loyalty/sequences")
async def create_loyalty_sequence(req: LoyaltySequenceCreate, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), **req.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.loyalty_sequences.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/loyalty/sequences/{sequence_id}")
async def update_loyalty_sequence(sequence_id: str, req: LoyaltySequenceCreate, user=Depends(get_current_user)):
    await db.loyalty_sequences.update_one({"id": sequence_id}, {"$set": req.model_dump()})
    sequence = await db.loyalty_sequences.find_one({"id": sequence_id}, {"_id": 0})
    return sequence


@router.delete("/loyalty/sequences/{sequence_id}")
async def delete_loyalty_sequence(sequence_id: str, user=Depends(get_current_user)):
    await db.loyalty_sequences.delete_one({"id": sequence_id})
    await db.loyalty_enrollments.delete_many({"sequence_id": sequence_id})
    return {"message": "Secuencia eliminada"}


@router.get("/loyalty/enrollments")
async def get_loyalty_enrollments(user=Depends(get_current_user)):
    enrollments = await db.loyalty_enrollments.find({}, {"_id": 0}).sort("enrolled_at", -1).to_list(500)
    return enrollments


@router.post("/loyalty/enroll")
async def enroll_lead_loyalty(lead_id: str = Query(...), sequence_id: str = Query(...), user=Depends(get_current_user)):
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    seq = await db.loyalty_sequences.find_one({"id": sequence_id}, {"_id": 0})
    if not seq:
        raise HTTPException(status_code=404, detail="Secuencia no encontrada")

    existing = await db.loyalty_enrollments.find_one({"lead_id": lead_id, "sequence_id": sequence_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Lead ya esta inscrito en esta secuencia")

    first_msg = seq["messages"][0] if seq.get("messages") else None
    first_delay = first_msg.get("delay_days", 1) if first_msg else 1

    enrollment = {
        "id": str(uuid.uuid4()),
        "lead_id": lead_id,
        "lead_name": lead.get("name", ""),
        "sequence_id": sequence_id,
        "sequence_name": seq.get("product_name", ""),
        "current_step": 0,
        "status": "active",
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
        "last_message_sent": None,
        "next_message_date": (datetime.now(timezone.utc) + timedelta(days=first_delay)).isoformat()
    }
    await db.loyalty_enrollments.insert_one(enrollment)
    enrollment.pop("_id", None)
    return enrollment


@router.delete("/loyalty/enrollments/{enrollment_id}")
async def delete_enrollment(enrollment_id: str, user=Depends(get_current_user)):
    await db.loyalty_enrollments.delete_one({"id": enrollment_id})
    return {"message": "Inscripcion eliminada"}


@router.post("/loyalty/process")
async def process_loyalty_messages(user=Depends(get_current_user)):
    wa_config = await get_whatsapp_config()
    wa_ready = wa_config and wa_config.get("phone_number_id") and wa_config.get("access_token")

    now = datetime.now(timezone.utc)
    enrollments = await db.loyalty_enrollments.find(
        {"status": "active", "next_message_date": {"$lte": now.isoformat()}},
        {"_id": 0}
    ).to_list(100)

    processed = 0
    completed = 0
    skipped = 0
    for e in enrollments:
        seq = await db.loyalty_sequences.find_one({"id": e["sequence_id"]}, {"_id": 0})
        if not seq or not seq.get("messages"):
            continue
        step = e.get("current_step", 0)
        if step >= len(seq["messages"]):
            await db.loyalty_enrollments.update_one({"id": e["id"]}, {"$set": {"status": "completed"}})
            completed += 1
            continue
        msg_config = seq["messages"][step]
        lead = await db.leads.find_one({"id": e["lead_id"]}, {"_id": 0})
        if not lead:
            continue
        phone = lead.get("whatsapp", "")
        if not phone:
            skipped += 1
            continue
        lead_name = lead.get("name", "").split()[0] if lead.get("name") else ""
        msg_text = msg_config.get("content", "").replace("{nombre}", lead_name)
        wa_template = msg_config.get("wa_template_name", "")

        wa_sent = False
        if wa_ready:
            if wa_template:
                wa_sent = await send_whatsapp_template(phone, wa_template, msg_config.get("wa_template_language", "es"), [lead_name or "cliente"])
            elif msg_text:
                wa_sent = await send_whatsapp_message(phone, msg_text)

        if wa_sent:
            session_id = f"wa_{phone}"
            await db.chat_messages.insert_one({
                "id": str(uuid.uuid4()), "session_id": session_id, "lead_id": lead["id"],
                "role": "assistant", "content": msg_text, "timestamp": now.isoformat(),
                "source": "loyalty"
            })

        next_step = step + 1
        if next_step >= len(seq["messages"]):
            await db.loyalty_enrollments.update_one(
                {"id": e["id"]},
                {"$set": {"status": "completed", "current_step": next_step, "last_message_sent": now.isoformat()}}
            )
            completed += 1
        else:
            next_delay = seq["messages"][next_step].get("delay_days", 1)
            await db.loyalty_enrollments.update_one(
                {"id": e["id"]},
                {"$set": {"current_step": next_step, "last_message_sent": now.isoformat(),
                          "next_message_date": (now + timedelta(days=next_delay)).isoformat()}}
            )
        processed += 1
        await db.leads.update_one({"id": lead["id"]}, {"$set": {"last_interaction": now.isoformat()}})

    pending = await db.loyalty_enrollments.count_documents({"status": "active"})
    return {"message": f"{processed} mensajes procesados, {completed} secuencias completadas, {skipped} sin WA", "processed": processed, "completed": completed, "skipped": skipped, "pending": pending}


@router.get("/loyalty/metrics")
async def get_loyalty_metrics(user=Depends(get_current_user)):
    total_enrollments = await db.loyalty_enrollments.count_documents({})
    active_enrollments = await db.loyalty_enrollments.count_documents({"status": "active"})
    completed_enrollments = await db.loyalty_enrollments.count_documents({"status": "completed"})

    sequences = await db.loyalty_sequences.find({}, {"_id": 0}).to_list(100)
    seq_metrics = []
    for seq in sequences:
        enrolled = await db.loyalty_enrollments.count_documents({"sequence_id": seq["id"]})
        active = await db.loyalty_enrollments.count_documents({"sequence_id": seq["id"], "status": "active"})
        done = await db.loyalty_enrollments.count_documents({"sequence_id": seq["id"], "status": "completed"})
        seq_metrics.append({
            "id": seq["id"], "name": seq.get("product_name", ""), "total_enrolled": enrolled,
            "active": active, "completed": done,
            "total_messages": len(seq.get("messages", [])),
            "completion_rate": round((done / enrolled * 100) if enrolled > 0 else 0, 1)
        })

    # Recompra analysis
    pipeline = [
        {"$match": {"funnel_stage": {"$in": ["cliente_nuevo", "cliente_activo"]}}},
        {"$project": {"purchase_count": {"$size": {"$ifNull": ["$purchase_history", []]}}, "name": 1, "id": 1}},
        {"$match": {"purchase_count": {"$gte": 2}}},
        {"$count": "repeat_buyers"}
    ]
    repeat = await db.leads.aggregate(pipeline).to_list(1)
    repeat_buyers = repeat[0]["repeat_buyers"] if repeat else 0

    total_clients = await db.leads.count_documents({"funnel_stage": {"$in": ["cliente_nuevo", "cliente_activo"]}})

    # Top repeat buyers
    top_pipeline = [
        {"$match": {"funnel_stage": {"$in": ["cliente_nuevo", "cliente_activo"]}}},
        {"$project": {
            "_id": 0, "id": 1, "name": 1, "whatsapp": 1,
            "purchase_count": {"$size": {"$ifNull": ["$purchase_history", []]}},
            "total_spent": {"$sum": {"$ifNull": ["$purchase_history.price", []]}}
        }},
        {"$sort": {"purchase_count": -1}},
        {"$limit": 10}
    ]
    top_buyers = await db.leads.aggregate(top_pipeline).to_list(10)

    # Churn risk (active but no interaction > 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    churn_risk = await db.leads.count_documents({
        "funnel_stage": {"$in": ["cliente_nuevo", "cliente_activo"]},
        "last_interaction": {"$lte": thirty_days_ago}
    })

    return {
        "total_enrollments": total_enrollments,
        "active_enrollments": active_enrollments,
        "completed_enrollments": completed_enrollments,
        "sequences": seq_metrics,
        "repeat_buyers": repeat_buyers,
        "total_clients": total_clients,
        "recompra_rate": round((repeat_buyers / total_clients * 100) if total_clients > 0 else 0, 1),
        "top_buyers": top_buyers,
        "churn_risk_count": churn_risk
    }


@router.post("/loyalty/auto-enroll-config")
async def set_auto_enroll_config(body: dict, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    config = {
        "id": "auto_enroll_config",
        "enabled": body.get("enabled", False),
        "target_stage": body.get("target_stage", "cliente_nuevo"),
        "default_sequence_id": body.get("default_sequence_id", ""),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.system_config.update_one({"id": "auto_enroll_config"}, {"$set": config}, upsert=True)
    return config


@router.get("/loyalty/auto-enroll-config")
async def get_auto_enroll_config(user=Depends(get_current_user)):
    config = await db.system_config.find_one({"id": "auto_enroll_config"}, {"_id": 0})
    return config or {"id": "auto_enroll_config", "enabled": False, "target_stage": "cliente_nuevo", "default_sequence_id": ""}
