from fastapi import APIRouter, HTTPException, Depends
import uuid
import re
import os
import logging
from datetime import datetime, timezone, timedelta
from database import db
from auth import get_current_user
from models import ChatMessageRequest, CRMWhatsAppReply
from utils import FUNNEL_STAGES
from whatsapp_utils import send_whatsapp_message
from bot_logic import build_product_bot_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


async def _resolve_chat_lead(session_id: str, lead_id: str = None):
    session_meta = await db.chat_sessions_meta.find_one({"session_id": session_id}, {"_id": 0})
    lead = None
    has_name = False
    if session_meta and session_meta.get("lead_id"):
        lead = await db.leads.find_one({"id": session_meta["lead_id"]}, {"_id": 0})
        if lead:
            has_name = True
    elif lead_id:
        lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
        if lead:
            has_name = True
            await db.chat_sessions_meta.update_one(
                {"session_id": session_id},
                {"$set": {"session_id": session_id, "lead_id": lead["id"], "lead_name": lead.get("name", "")}},
                upsert=True
            )
    return lead, has_name


async def _parse_ai_response(assistant_content: str, has_name: bool, lead_id_for_session, session_id: str):
    name_match = re.search(r'\[LEAD_NAME:([^\]]+)\]', assistant_content)
    if name_match and not has_name:
        detected_name = name_match.group(1).strip()
        assistant_content = re.sub(r'\[LEAD_NAME:[^\]]+\]', '', assistant_content).strip()
        new_lead = {
            "id": str(uuid.uuid4()), "name": detected_name, "whatsapp": "", "city": "", "email": "",
            "product_interest": "", "source": "Chat IA", "game_used": None, "prize_obtained": None,
            "funnel_stage": "nuevo", "status": "activo", "purchase_history": [], "coupon_used": None,
            "recompra_date": None, "notes": "Registrado via Chat IA",
            "last_interaction": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.leads.insert_one(new_lead)
        lead_id_for_session = new_lead["id"]
        await db.chat_sessions_meta.update_one(
            {"session_id": session_id},
            {"$set": {"session_id": session_id, "lead_id": new_lead["id"], "lead_name": detected_name}},
            upsert=True
        )
        await db.chat_messages.update_many(
            {"session_id": session_id, "lead_id": None}, {"$set": {"lead_id": new_lead["id"]}}
        )
        logger.info(f"New lead created from chat: {detected_name} -> {new_lead['id']}")

    update_matches = re.findall(r'\[UPDATE_LEAD:(\w+)=([^\]]+)\]', assistant_content)
    if update_matches and lead_id_for_session:
        update_fields = {}
        for field, value in update_matches:
            if field in {"whatsapp", "city", "product_interest", "email"}:
                update_fields[field] = value.strip()
        if update_fields:
            update_fields["last_interaction"] = datetime.now(timezone.utc).isoformat()
            await db.leads.update_one({"id": lead_id_for_session}, {"$set": update_fields})
            logger.info(f"Lead {lead_id_for_session} updated via chat: {update_fields}")
        assistant_content = re.sub(r'\[UPDATE_LEAD:\w+=[^\]]+\]', '', assistant_content).strip()

    stage_match = re.search(r'\[STAGE:(\w+)\]', assistant_content)
    if stage_match:
        new_stage = stage_match.group(1).strip()
        assistant_content = re.sub(r'\[STAGE:\w+\]', '', assistant_content).strip()
        if new_stage in FUNNEL_STAGES and lead_id_for_session:
            await db.leads.update_one(
                {"id": lead_id_for_session},
                {"$set": {"funnel_stage": new_stage, "last_interaction": datetime.now(timezone.utc).isoformat()}}
            )

    return assistant_content, lead_id_for_session


@router.post("/chat/message")
async def send_chat_message(req: ChatMessageRequest, user=Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    products = await db.products.find({"active": True}, {"_id": 0}).to_list(100)
    product_info = "\n".join([f"- {p['name']}: ${p['price']} - {p.get('description', '')}" for p in products])

    lead, has_name = await _resolve_chat_lead(req.session_id, req.lead_id)
    lead_name = lead.get("name", "") if lead else ""

    pending_quote = ""
    if lead:
        quote = await db.quotations.find_one({"lead_id": lead["id"], "status": "pendiente"}, {"_id": 0})
        if quote:
            pending_quote = f"\nEste cliente tiene una cotizacion pendiente por ${quote['total']:.2f}. Pregunta si desea continuar con ella."

    product_interest = lead.get("product_interest", "") if lead else ""
    product_specific_prompt = None
    if product_interest:
        product_specific_prompt = await build_product_bot_prompt(product_interest, products, lead or {})

    if product_specific_prompt:
        system_msg = product_specific_prompt + (f"\n{pending_quote}" if pending_quote else "")
    else:
        name_instruction = ""
        if not has_name:
            name_instruction = """
IMPORTANTE - REGISTRO DE LEAD:
- Este es un lead NUEVO. Saluda cordialmente y pregunta su nombre completo.
- Una vez que proporcione su nombre, confirma diciendo su nombre y pregunta su numero de WhatsApp.
- Despues pregunta su ciudad y que producto le interesa.
- Cuando el usuario diga su nombre, incluye al FINAL de tu respuesta (en una linea separada): [LEAD_NAME:Nombre Apellido]
- Solo incluye [LEAD_NAME:] cuando el usuario efectivamente diga su nombre.
- Recopila los datos uno por uno de forma natural, no todos de golpe."""
        else:
            missing_fields = []
            if lead and not lead.get("whatsapp"):
                missing_fields.append("numero de WhatsApp")
            if lead and not lead.get("city"):
                missing_fields.append("ciudad")
            if lead and not lead.get("product_interest"):
                missing_fields.append("que producto le interesa")
            missing_instruction = ""
            if missing_fields:
                missing_instruction = f"\nDATOS FALTANTES DEL CLIENTE: Necesitas preguntarle su {', '.join(missing_fields)}. Hazlo de forma natural durante la conversacion."
                missing_instruction += "\nCuando el cliente proporcione datos, incluye al final: [UPDATE_LEAD:campo=valor] donde campo puede ser: whatsapp, city, product_interest"
            name_instruction = f"\nEl cliente se llama {lead_name}. Usa su nombre de forma natural en la conversacion.{missing_instruction}"

        system_msg = f"""Eres el Asesor Virtual Oficial de Fakulti Laboratorios (marca Fakulti).
Tu funcion: Atender leads, calificar, cotizar y cerrar venta.
{name_instruction}
{pending_quote}

PRODUCTOS DISPONIBLES:
{product_info}

REGLAS:
- Nunca sonar robot. Se amigable y profesional.
- Nunca hacer promesas medicas.
- Nunca afirmar que cura enfermedades.
- Nunca recomendar reemplazar tratamiento medico.
- Bombro es Bone Broth Hidrolizado, producto unico en Ecuador.
- Responde siempre en espanol.
- Se conciso pero util.
- Si el usuario pide precio, proporciona la informacion.
- Si pide comprar, indica los pasos.

DETECCION DE PRODUCTO:
Cuando identifiques que producto le interesa al cliente, incluye: [UPDATE_LEAD:product_interest=NombreProducto]

CLASIFICACION AUTOMATICA:
Al final de CADA respuesta, incluye en una linea separada la etapa del lead:
[STAGE:nuevo] - Primer contacto, aun no muestra interes especifico
[STAGE:interesado] - Pregunta por productos, precios o beneficios
[STAGE:en_negociacion] - Solicita cotizacion, forma de pago, envio o stock
[STAGE:cliente_nuevo] - Confirma compra
[STAGE:perdido] - Dice que no le interesa o rechaza explicitamente

Incluye SIEMPRE el tag [STAGE:] al final."""

    history = await db.chat_messages.find(
        {"session_id": req.session_id}, {"_id": 0}
    ).sort("timestamp", 1).limit(20).to_list(20)

    llm_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(api_key=llm_key, session_id=req.session_id, system_message=system_msg)
    chat.with_model("openai", "gpt-5.2")

    for msg in history:
        if msg["role"] == "user":
            chat.messages.append({"role": "user", "content": msg["content"]})
        else:
            chat.messages.append({"role": "assistant", "content": msg["content"]})

    user_msg_doc = {
        "id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "lead_id": req.lead_id or (lead["id"] if lead else None),
        "role": "user",
        "content": req.message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(user_msg_doc)

    try:
        response = await chat.send_message(UserMessage(text=req.message))
        assistant_content = response if isinstance(response, str) else str(response)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        assistant_content = "Disculpa, tuve un problema tecnico. Puedes repetir tu consulta?"

    lead_id_for_session = req.lead_id or (lead["id"] if lead else None)
    assistant_content, lead_id_for_session = await _parse_ai_response(
        assistant_content, has_name, lead_id_for_session, req.session_id
    )

    assistant_msg_doc = {
        "id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "lead_id": lead_id_for_session,
        "role": "assistant",
        "content": assistant_content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(assistant_msg_doc)

    lead_info = None
    if lead_id_for_session:
        lead_doc = await db.leads.find_one({"id": lead_id_for_session}, {"_id": 0})
        if lead_doc:
            lead_info = {"id": lead_doc["id"], "name": lead_doc["name"], "funnel_stage": lead_doc["funnel_stage"]}

    return {"response": assistant_content, "session_id": req.session_id, "lead": lead_info}


@router.delete("/chat/messages/{message_id}")
async def delete_chat_message(message_id: str, user=Depends(get_current_user)):
    result = await db.chat_messages.delete_one({"id": message_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    return {"message": "Mensaje eliminado"}


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, user=Depends(get_current_user)):
    result = await db.chat_messages.delete_many({"session_id": session_id})
    await db.chat_sessions_meta.delete_one({"session_id": session_id})
    return {"message": f"Conversacion eliminada ({result.deleted_count} mensajes)"}


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, user=Depends(get_current_user)):
    messages = await db.chat_messages.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)
    return messages


@router.get("/chat/sessions")
async def get_chat_sessions(user=Depends(get_current_user)):
    pipeline = [
        {"$group": {"_id": "$session_id", "lead_id": {"$first": "$lead_id"}, "last_message": {"$last": "$content"}, "timestamp": {"$last": "$timestamp"}, "count": {"$sum": 1}}},
        {"$sort": {"timestamp": -1}},
        {"$limit": 50}
    ]
    sessions = await db.chat_messages.aggregate(pipeline).to_list(50)
    user_role = user.get("role", "admin")
    user_id = user["id"]
    result = []
    for s in sessions:
        meta = await db.chat_sessions_meta.find_one({"session_id": s["_id"]}, {"_id": 0})
        lead_name = meta.get("lead_name", "") if meta else ""
        source = meta.get("source", "chat_ia") if meta else "chat_ia"
        # Fallback: sessions with wa_ prefix are always WhatsApp (defensive check
        # in case chat_sessions_meta was not created or missing source field)
        if source != "whatsapp" and s["_id"].startswith("wa_"):
            source = "whatsapp"
        lead_phone = ""
        lead_channel = ""
        bot_paused = False
        has_alert = False
        assigned_advisor = ""
        needs_advisor = False
        if source == "whatsapp" and s.get("lead_id"):
            lead_doc = await db.leads.find_one({"id": s["lead_id"]}, {"_id": 0, "whatsapp": 1, "name": 1, "channel": 1, "bot_paused": 1, "assigned_advisor": 1, "needs_advisor": 1, "funnel_stage": 1})
            if lead_doc:
                lead_phone = lead_doc.get("whatsapp", "")
                lead_channel = lead_doc.get("channel", "")
                bot_paused = lead_doc.get("bot_paused", False)
                assigned_advisor = lead_doc.get("assigned_advisor", "")
                needs_advisor = lead_doc.get("needs_advisor", False) and not assigned_advisor
                if not lead_name:
                    lead_name = lead_doc.get("name", "")
            alert = await db.handover_alerts.find_one({"lead_id": s["lead_id"], "status": "pending"}, {"_id": 0})
            has_alert = alert is not None
        if user_role == "advisor" and assigned_advisor != user_id:
            continue
        # Unread count = user messages received after last time someone opened this session
        last_seen_at = meta.get("last_seen_at") if meta else None
        if last_seen_at:
            unread_count = await db.chat_messages.count_documents({
                "session_id": s["_id"], "role": "user", "timestamp": {"$gt": last_seen_at}
            })
        else:
            unread_count = await db.chat_messages.count_documents({
                "session_id": s["_id"], "role": "user"
            })
        result.append({
            "session_id": s["_id"], "lead_id": s.get("lead_id"), "lead_name": lead_name,
            "last_message": s["last_message"], "timestamp": s["timestamp"], "message_count": s["count"],
            "source": source, "lead_phone": lead_phone, "lead_channel": lead_channel, "bot_paused": bot_paused, "has_alert": has_alert,
            "assigned_advisor": assigned_advisor, "needs_advisor": needs_advisor,
            "unread_count": unread_count
        })
    return result


@router.post("/chat/sessions/{session_id}/mark-read")
async def mark_session_read(session_id: str, user=Depends(get_current_user)):
    """Marca la sesion como leida actualizando last_seen_at en chat_sessions_meta."""
    now = datetime.now(timezone.utc).isoformat()
    await db.chat_sessions_meta.update_one(
        {"session_id": session_id},
        {"$set": {"last_seen_at": now}},
        upsert=True
    )
    return {"success": True, "last_seen_at": now}


@router.get("/chat/lead-session/{lead_id}")
async def get_or_create_lead_session(lead_id: str, user=Depends(get_current_user)):
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    if lead.get("assigned_advisor"):
        advisor = await db.admin_users.find_one({"id": lead["assigned_advisor"], "role": "advisor"}, {"_id": 0, "name": 1})
        lead["_advisor_name"] = advisor["name"] if advisor else ""
    meta = await db.chat_sessions_meta.find_one({"lead_id": lead_id}, {"_id": 0})
    if meta:
        msgs = await db.chat_messages.find({"session_id": meta["session_id"]}, {"_id": 0}).sort("timestamp", 1).to_list(100)
        return {"session_id": meta["session_id"], "lead": lead, "messages": msgs, "is_new": False}
    new_sid = f"lead_{lead_id}_{int(datetime.now(timezone.utc).timestamp())}"
    await db.chat_sessions_meta.insert_one({"session_id": new_sid, "lead_id": lead_id, "lead_name": lead.get("name", "")})
    return {"session_id": new_sid, "lead": lead, "messages": [], "is_new": True}


@router.get("/chat/whatsapp-stats")
async def get_whatsapp_stats(user=Depends(get_current_user)):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    active_sessions = await db.chat_sessions_meta.count_documents({"source": "whatsapp", "last_activity": {"$gte": cutoff}})
    total_wa_sessions = await db.chat_sessions_meta.count_documents({"source": "whatsapp"})

    pipeline = [
        {"$match": {"source": "whatsapp", "role": "assistant", "response_time_ms": {"$exists": True}}},
        {"$sort": {"timestamp": -1}},
        {"$limit": 50},
        {"$group": {"_id": None, "avg_response_ms": {"$avg": "$response_time_ms"}, "min_response_ms": {"$min": "$response_time_ms"}, "max_response_ms": {"$max": "$response_time_ms"}}}
    ]
    stats = await db.chat_messages.aggregate(pipeline).to_list(1)
    avg_ms = int(stats[0]["avg_response_ms"]) if stats else 0

    pending_alerts = await db.handover_alerts.count_documents({"status": "pending"})
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
    messages_today = await db.chat_messages.count_documents({"source": "whatsapp", "timestamp": {"$gte": today_start}})

    delivered = await db.chat_messages.count_documents({"source": "whatsapp", "role": "assistant", "delivered": True})
    failed = await db.chat_messages.count_documents({"source": "whatsapp", "role": "assistant", "delivered": False})

    return {
        "active_conversations_24h": active_sessions,
        "total_conversations": total_wa_sessions,
        "avg_response_time_ms": avg_ms,
        "pending_alerts": pending_alerts,
        "messages_today": messages_today,
        "delivered": delivered,
        "failed": failed
    }


@router.get("/chat/alerts")
async def get_handover_alerts(user=Depends(get_current_user)):
    alerts = await db.handover_alerts.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    for a in alerts:
        if a.get("lead_id"):
            lead = await db.leads.find_one({"id": a["lead_id"]}, {"_id": 0, "name": 1, "whatsapp": 1, "product_interest": 1, "channel": 1, "city": 1, "funnel_stage": 1, "bot_paused": 1})
            if lead:
                a["lead_name"] = lead.get("name", a.get("lead_name", ""))
                a["lead_product"] = lead.get("product_interest", "")
                a["lead_channel"] = lead.get("channel", "")
                a["lead_city"] = lead.get("city", "")
                a["lead_stage"] = lead.get("funnel_stage", "")
                a["bot_paused"] = lead.get("bot_paused", False)
    return alerts


@router.put("/chat/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user=Depends(get_current_user)):
    result = await db.handover_alerts.update_one(
        {"id": alert_id},
        {"$set": {"status": "resolved", "resolved_at": datetime.now(timezone.utc).isoformat(), "resolved_by": "admin"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return {"message": "Alerta resuelta"}


@router.post("/chat/whatsapp-reply")
async def crm_whatsapp_reply(req: CRMWhatsAppReply, user=Depends(get_current_user)):
    lead = await db.leads.find_one({"id": req.lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    phone = lead.get("whatsapp", "")
    if not phone:
        raise HTTPException(status_code=400, detail="Lead no tiene numero de WhatsApp")

    sent = await send_whatsapp_message(phone, req.message)
    if not sent:
        raise HTTPException(status_code=500, detail="Error al enviar mensaje")

    session_id = f"wa_{phone}"
    now = datetime.now(timezone.utc).isoformat()
    await db.chat_messages.insert_one({
        "id": str(uuid.uuid4()), "session_id": session_id, "lead_id": req.lead_id,
        "role": "assistant", "content": req.message, "timestamp": now,
        "source": "whatsapp", "sent_by": "crm_agent", "delivered": sent
    })
    await db.chat_sessions_meta.update_one(
        {"session_id": session_id},
        {"$set": {"last_activity": now}},
        upsert=True
    )
    return {"message": "Mensaje enviado", "delivered": sent}


@router.post("/chat/analyze/{session_id}")
async def analyze_conversation(session_id: str, user=Depends(get_current_user)):
    msgs = await db.chat_messages.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)
    if not msgs:
        raise HTTPException(status_code=404, detail="Sin mensajes para analizar")

    conversation_text = "\n".join([f"{'Cliente' if m['role'] == 'user' else 'Bot/Agente'}: {m['content']}" for m in msgs[-30:]])

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import uuid as uuid_module

        system_message = """Eres un asistente de analisis de conversaciones para Fakulti (productos naturales).
Analiza la conversacion entre un cliente y el bot/agente. Responde SIEMPRE en espanol con el siguiente formato JSON:
{
  "resumen": "Resumen conciso de la conversacion (maximo 3 oraciones)",
  "sentimiento": "positivo|neutral|negativo",
  "interes_producto": "producto mencionado o 'no identificado'",
  "etapa_sugerida": "nuevo|interesado|en_negociacion|cliente_nuevo|perdido",
  "respuestas_sugeridas": ["respuesta sugerida 1", "respuesta sugerida 2", "respuesta sugerida 3"],
  "temas_clave": ["tema1", "tema2"],
  "nivel_urgencia": "alto|medio|bajo"
}"""

        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        llm_session_id = str(uuid_module.uuid4())

        llm = LlmChat(api_key=api_key, session_id=llm_session_id, system_message=system_message)
        llm = llm.with_model(provider="openai", model="gpt-5.2")

        user_message_text = f"Analiza esta conversacion:\n\n{conversation_text}"
        user_message = UserMessage(text=user_message_text)
        response_text = await llm.send_message(user_message)

        import json as json_module
        try:
            text = response_text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                analysis = json_module.loads(text[start:end])
            else:
                analysis = {"resumen": text, "sentimiento": "neutral", "respuestas_sugeridas": [], "temas_clave": [], "nivel_urgencia": "medio"}
        except Exception:
            analysis = {"resumen": response_text, "sentimiento": "neutral", "respuestas_sugeridas": [], "temas_clave": [], "nivel_urgencia": "medio"}

        return analysis
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Error en analisis IA: {str(e)}")
