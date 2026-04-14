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
    from utils import STAGE_LABELS

    # === SUMMARY ===
    total_leads = await db.leads.count_documents({})
    converted = await db.leads.count_documents({"funnel_stage": {"$in": ["cliente_nuevo", "cliente_activo"]}})
    in_progress = await db.leads.count_documents({"funnel_stage": {"$in": ["interesado", "en_negociacion"]}})
    lost = await db.leads.count_documents({"funnel_stage": "perdido"})
    conversion_rate = round((converted / total_leads * 100) if total_leads > 0 else 0, 1)

    total_sessions = await db.chat_sessions_meta.count_documents({})
    bot_messages = await db.chat_messages.count_documents({"role": "assistant"})
    user_messages = await db.chat_messages.count_documents({"role": "user"})
    total_campaign_sends = 0
    campaigns_data = await db.campaigns.find({}, {"_id": 0, "name": 1, "sent_count": 1, "failed_count": 1, "status": 1}).to_list(100)
    for c in campaigns_data:
        total_campaign_sends += c.get("sent_count", 0)

    summary = {
        "total_leads": total_leads,
        "conversion_rate": conversion_rate,
        "total_sessions": total_sessions,
        "bot_messages": bot_messages,
        "user_messages": user_messages,
        "total_campaign_sends": total_campaign_sends,
        "converted": converted,
        "in_progress": in_progress,
        "lost": lost,
    }

    # === FUNNEL DISTRIBUTION ===
    funnel_stages = ["nuevo", "interesado", "en_negociacion", "cliente_nuevo", "cliente_activo", "perdido"]
    funnel_distribution = []
    for stage in funnel_stages:
        count = await db.leads.count_documents({"funnel_stage": stage})
        funnel_distribution.append({"stage": STAGE_LABELS.get(stage, stage), "count": count})

    # === PRODUCT INTEREST ===
    product_pipeline = [
        {"$match": {"product_interest": {"$ne": ""}}},
        {"$group": {"_id": "$product_interest", "leads": {"$sum": 1}}},
        {"$sort": {"leads": -1}},
        {"$limit": 10}
    ]
    product_interest_raw = await db.leads.aggregate(product_pipeline).to_list(10)
    product_interest = [{"product": p["_id"], "leads": p["leads"]} for p in product_interest_raw]

    # === PRODUCT REVENUE ===
    revenue_pipeline = [
        {"$unwind": "$purchase_history"},
        {"$group": {"_id": "$purchase_history.product_name", "revenue": {"$sum": "$purchase_history.price"}, "count": {"$sum": 1}}},
        {"$sort": {"revenue": -1}},
        {"$limit": 10}
    ]
    revenue_raw = await db.leads.aggregate(revenue_pipeline).to_list(10)
    product_revenue = [{"product": r["_id"], "revenue": round(r["revenue"], 2), "orders": r["count"]} for r in revenue_raw]

    # === LOYALTY ===
    total_enrollments = await db.loyalty_enrollments.count_documents({})
    active_enrollments = await db.loyalty_enrollments.count_documents({"status": "active"})
    completed_enrollments = await db.loyalty_enrollments.count_documents({"status": "completed"})
    sent_loyalty_msgs = await db.chat_messages.count_documents({"source": "loyalty"})
    total_loyalty_msgs = 0
    sequences = await db.loyalty_sequences.find({}, {"_id": 0}).to_list(100)
    for seq in sequences:
        total_loyalty_msgs += len(seq.get("messages", []))

    loyalty = {
        "total_enrollments": total_enrollments,
        "active_enrollments": active_enrollments,
        "completed_enrollments": completed_enrollments,
        "sent_messages": sent_loyalty_msgs,
        "total_messages": total_loyalty_msgs,
    }

    # === SEQUENCE EFFECTIVENESS ===
    sequence_effectiveness = []
    for seq in sequences:
        enrolled = await db.loyalty_enrollments.count_documents({"sequence_id": seq["id"]})
        done = await db.loyalty_enrollments.count_documents({"sequence_id": seq["id"], "status": "completed"})
        comp_rate = round((done / enrolled * 100) if enrolled > 0 else 0, 1)
        sequence_effectiveness.append({
            "name": seq.get("product_name", ""),
            "enrollments": enrolled,
            "completion_rate": comp_rate,
            "delivery_rate": 100 if enrolled > 0 else 0,
        })

    # === CAMPAIGNS ===
    campaigns_list = [{"name": c.get("name", ""), "sent": c.get("sent_count", 0), "failed": c.get("failed_count", 0), "status": c.get("status", "draft")} for c in campaigns_data]

    # === TOP BUYERS ===
    top_pipeline = [
        {"$match": {"purchase_history": {"$exists": True, "$ne": []}}},
        {"$project": {
            "_id": 0, "id": 1, "name": 1, "whatsapp": 1, "funnel_stage": 1,
            "purchase_count": {"$size": "$purchase_history"},
            "total_spent": {"$sum": "$purchase_history.price"}
        }},
        {"$sort": {"purchase_count": -1}},
        {"$limit": 10}
    ]
    top_raw = await db.leads.aggregate(top_pipeline).to_list(10)
    top_buyers = [{"name": b.get("name", ""), "purchases": b.get("purchase_count", 0), "total_spent": round(b.get("total_spent", 0), 2), "stage": STAGE_LABELS.get(b.get("funnel_stage", ""), b.get("funnel_stage", ""))} for b in top_raw]

    return {
        "summary": summary,
        "funnel_distribution": funnel_distribution,
        "product_interest": product_interest,
        "product_revenue": product_revenue,
        "loyalty": loyalty,
        "sequence_effectiveness": sequence_effectiveness,
        "campaigns": campaigns_list,
        "top_buyers": top_buyers,
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
