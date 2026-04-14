from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from fastapi.responses import PlainTextResponse, FileResponse
import uuid
import re
import os
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from database import db
from auth import get_current_user
from utils import normalize_phone_ec, find_lead_by_phone, FUNNEL_STAGES
from whatsapp_utils import (
    get_whatsapp_config, send_whatsapp_message, send_whatsapp_image,
    send_whatsapp_template, WHATSAPP_API_URL, HANDOVER_KEYWORDS,
    BOT_TRANSFER_PHRASES, BOT_TIMEOUT_SECONDS
)
from bot_logic import build_product_bot_prompt
from models import WhatsAppMessage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


async def detect_channel_from_message(message_text: str, lead_id: str):
    msg_lower = message_text.strip().lower()
    campaigns = await db.qr_campaigns.find({"active": True}, {"_id": 0}).to_list(50)
    for campaign in campaigns:
        campaign_msg = campaign["initial_message"].strip().lower()
        if msg_lower == campaign_msg or campaign_msg in msg_lower:
            update = {
                "channel": campaign.get("channel", ""),
                "source": campaign.get("source", ""),
                "last_interaction": datetime.now(timezone.utc).isoformat()
            }
            if campaign.get("product"):
                update["product_interest"] = campaign["product"]
            await db.leads.update_one({"id": lead_id}, {"$set": update})
            await db.qr_campaigns.update_one({"id": campaign["id"]}, {"$inc": {"scan_count": 1}})
            logger.info(f"QR campaign matched for lead {lead_id}: {campaign['name']} -> channel={campaign['channel']}")
            return True
    return False


async def process_whatsapp_incoming(phone: str, message_text: str):
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    phone = normalize_phone_ec(phone)
    existing_lead = await find_lead_by_phone(phone)

    if existing_lead and existing_lead.get("whatsapp") != phone:
        await db.leads.update_one({"id": existing_lead["id"]}, {"$set": {"whatsapp": phone}})
        existing_lead["whatsapp"] = phone

    is_new = existing_lead is None
    lead_id = existing_lead["id"] if existing_lead else None
    lead_name = existing_lead.get("name", "") if existing_lead else ""

    if existing_lead and existing_lead.get("bot_paused"):
        session_id = f"wa_{phone}"
        now = datetime.now(timezone.utc).isoformat()
        await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "session_id": session_id, "lead_id": lead_id, "role": "user", "content": message_text, "timestamp": now, "source": "whatsapp"})
        await db.chat_sessions_meta.update_one(
            {"session_id": session_id},
            {"$set": {"session_id": session_id, "lead_id": lead_id, "lead_name": lead_name, "source": "whatsapp", "last_activity": now}},
            upsert=True
        )
        await db.leads.update_one({"id": lead_id}, {"$set": {"last_interaction": now}})
        logger.info(f"Bot paused for lead {lead_id} ({phone}) - message stored, no auto-reply")
        return "[BOT_PAUSED] Mensaje recibido. Un asesor humano tiene el control.", lead_id

    if is_new:
        new_lead = {
            "id": str(uuid.uuid4()), "name": "", "whatsapp": phone,
            "city": "", "email": "", "product_interest": "", "source": "WhatsApp",
            "season": "", "channel": "WhatsApp",
            "game_used": None, "prize_obtained": None, "funnel_stage": "nuevo", "status": "activo",
            "purchase_history": [], "coupon_used": None, "recompra_date": None,
            "notes": "Registrado via WhatsApp",
            "last_interaction": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.leads.insert_one(new_lead)
        lead_id = new_lead["id"]
        existing_lead = new_lead
        await detect_channel_from_message(message_text, lead_id)
        existing_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0}) or existing_lead
    elif not existing_lead.get("channel") or existing_lead.get("channel") == "WhatsApp":
        history_count = await db.chat_messages.count_documents({"session_id": f"wa_{phone}"})
        if history_count <= 2:
            detected = await detect_channel_from_message(message_text, lead_id)
            if detected:
                existing_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0}) or existing_lead

    products = await db.products.find({"active": True}, {"_id": 0}).to_list(100)
    product_info = "\n".join([f"- {p['name']}: ${p['price']} - {p.get('description', '')}" for p in products])

    session_id = f"wa_{phone}"
    history = await db.chat_messages.find(
        {"session_id": session_id}, {"_id": 0}
    ).sort("timestamp", 1).to_list(50)

    all_user_text = "\n".join([m["content"] for m in history if m.get("role") == "user"])

    conversation_data = []
    if existing_lead.get("name"):
        conversation_data.append(f"Nombre: {existing_lead['name']}")
    if existing_lead.get("city"):
        conversation_data.append(f"Ciudad: {existing_lead['city']}")
    if existing_lead.get("email"):
        conversation_data.append(f"Email: {existing_lead['email']}")
    if existing_lead.get("product_interest"):
        conversation_data.append(f"Producto de interes: {existing_lead['product_interest']}")
    conversation_data.append(f"WhatsApp: {phone}")

    import re as _re
    ci_matches = _re.findall(r'(?:cedula|ci|ruc|cedula)[:\s]*(\d{10,13})', all_user_text, _re.IGNORECASE)
    if not ci_matches:
        ci_matches = _re.findall(r'\b(\d{10})\b', all_user_text)
    if ci_matches:
        ci_val = ci_matches[-1]
        conversation_data.append(f"CI/RUC mencionado: {ci_val}")
        if lead_id and not existing_lead.get("ci_ruc"):
            await db.leads.update_one({"id": lead_id}, {"$set": {"ci_ruc": ci_val}})

    phone_matches = _re.findall(r'(?:telefono|numero|celular|contacto|cel)[:\s]*(09\d{8}|593\d{9})', all_user_text, _re.IGNORECASE)
    if not phone_matches:
        phone_matches = _re.findall(r'\b(09\d{8})\b', all_user_text)
    if phone_matches:
        conversation_data.append(f"Telefono contacto: {phone_matches[-1]}")

    addr_matches = _re.findall(r'(?:direccion|direccion|domicilio|entrega)[:\s]*(.{10,80})', all_user_text, _re.IGNORECASE)
    if addr_matches:
        conversation_data.append(f"Direccion: {addr_matches[-1].strip()}")
        if lead_id and not existing_lead.get("address"):
            await db.leads.update_one({"id": lead_id}, {"$set": {"address": addr_matches[-1].strip()}})
    list_addr = _re.findall(r'1\.\s*(.+(?:sauces|cdla|ciudadela|calle|mz|villa|manzana).+)', all_user_text, _re.IGNORECASE)
    if list_addr and not addr_matches:
        conversation_data.append(f"Direccion: {list_addr[-1].strip()}")
        if lead_id and not existing_lead.get("address"):
            await db.leads.update_one({"id": lead_id}, {"$set": {"address": list_addr[-1].strip()}})

    recent_msgs = history[-10:] if len(history) > 10 else history
    conversation_summary = "\n".join([f"{'CLIENTE' if m['role']=='user' else 'BOT'}: {m['content'][:200]}" for m in recent_msgs])

    collected_data_text = ""
    if conversation_data:
        collected_data_text = "\n\nDATOS YA PROPORCIONADOS POR EL CLIENTE (PROHIBIDO volver a solicitar):\n" + "\n".join(f"- {d}" for d in conversation_data)
    if conversation_summary:
        collected_data_text += f"\n\nRESUMEN ULTIMOS MENSAJES:\n{conversation_summary}"

    # Repetition detection
    bot_messages = [m["content"] for m in history if m.get("role") == "assistant"]
    repetition_keywords = ["direccion", "direccion", "cedula", "cedula", "contacto", "telefono", "telefono", "numero", "numero", "nombre completo"]
    ask_counts = {}
    for bm in bot_messages[-6:]:
        bm_lower = bm.lower()
        for kw in repetition_keywords:
            if kw in bm_lower and "?" in bm:
                ask_counts[kw] = ask_counts.get(kw, 0) + 1
    repeated_topics = [kw for kw, count in ask_counts.items() if count >= 2]
    if repeated_topics:
        advisor_id = existing_lead.get("assigned_advisor", "")
        await db.chat_alerts.insert_one({
            "id": str(uuid.uuid4()), "session_id": session_id, "lead_id": lead_id,
            "lead_name": existing_lead.get("name", phone), "type": "bot_confused",
            "message": f"Bot repite preguntas sobre: {', '.join(repeated_topics)}. Se requiere intervencion.",
            "resolved": False, "created_at": datetime.now(timezone.utc).isoformat()
        })
        if advisor_id:
            await db.advisor_notifications.insert_one({
                "id": str(uuid.uuid4()), "advisor_id": advisor_id, "type": "bot_escalation",
                "title": f"Bot necesita ayuda con {existing_lead.get('name', phone)}",
                "message": f"Bot repite preguntas sobre {', '.join(repeated_topics)}.",
                "lead_id": lead_id, "session_id": session_id, "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        logger.warning(f"Bot escalation: repetition for lead {lead_id} on: {repeated_topics}")
        collected_data_text += f"\n\nALERTA: Cliente YA proporciono {', '.join(repeated_topics)}. NO pidas estos datos. Si no puedes continuar, di: 'Un momento, te transfiero con un asesor.'"

    existing_lead["_collected_data_text"] = collected_data_text

    # Build system prompt
    product_interest = existing_lead.get("product_interest", "")
    product_specific_prompt = None
    if product_interest:
        product_specific_prompt = await build_product_bot_prompt(product_interest, products, existing_lead)

    if product_specific_prompt:
        system_msg = product_specific_prompt
    else:
        global_config = await db.bot_training.find_one({"id": "global"}, {"_id": 0}) or {}
        bot_name = global_config.get("bot_name", "Asesor Virtual Fakulti")
        brand_name = global_config.get("brand_name", "Fakulti")
        tone = global_config.get("tone", "Cercano, experto, humano, confiable. Ciencia + natural = Biotecnologia.")
        greeting_style = global_config.get("greeting_style", "Saluda con un emoji y pregunta el nombre del cliente.")
        farewell_style = global_config.get("farewell_style", "Despidete cordialmente y recuerda que estas disponible.")
        prohibited = global_config.get("prohibited_phrases", "No prometer curas. No afirmar que reemplaza tratamientos medicos.")
        general_inst = global_config.get("general_instructions", "")
        max_emojis = global_config.get("max_emojis_per_message", 2)
        max_lines = global_config.get("max_lines_per_message", 6)

        kb_entries = await db.knowledge_base.find({"active": True}, {"_id": 0, "question": 1, "answer": 1}).to_list(50)
        kb_text = ""
        if kb_entries:
            kb_text = "\n\nBASE DE CONOCIMIENTO (usa estas respuestas cuando aplique):\n" + "\n".join(
                [f"P: {e['question']}\nR: {e['answer']}" for e in kb_entries]
            )

        missing_fields = []
        if not lead_name:
            missing_fields.append("nombre y apellido")
        if not existing_lead.get("city"):
            missing_fields.append("ciudad")
        if not existing_lead.get("email"):
            missing_fields.append("email")
        if not existing_lead.get("product_interest"):
            missing_fields.append("producto de interes")

        data_context = ""
        if lead_name:
            data_context = f"\nEl cliente se llama {lead_name}."
            if existing_lead.get("city"):
                data_context += f" Ciudad: {existing_lead['city']}."
            if existing_lead.get("email"):
                data_context += f" Email: {existing_lead['email']}."
            if existing_lead.get("product_interest"):
                data_context += f" Interesado en: {existing_lead['product_interest']}."

        missing_instruction = ""
        if missing_fields:
            missing_instruction = f"\nDATOS QUE AUN FALTAN POR RECOPILAR: {', '.join(missing_fields)}. Recopilalos de forma natural durante la conversacion, uno a la vez, sin parecer formulario."

        first_contact = f"\nEste es un lead NUEVO. {greeting_style}" if not lead_name else ""

        system_msg = f"""IDENTIDAD DEL AGENTE
Eres {bot_name}, el asesor virtual de la marca {brand_name} por WhatsApp.
Representas los productos desarrollados por {brand_name} Laboratorios.
Tu tono y estilo: {tone}
Habla como persona real, no como robot. Frases cortas y faciles de entender.
Puedes usar emojis de forma natural (maximo {max_emojis} por mensaje).
Despedida: {farewell_style}
{first_contact}
{data_context}
{collected_data_text}
{missing_instruction}
{f"INSTRUCCIONES ADICIONALES DEL DESARROLLADOR: {general_inst}" if general_inst else ""}

REGLA CRITICA - NO REPETIR PREGUNTAS
Lee TODA la conversacion anterior antes de responder. Si el cliente YA proporciono un dato (nombre, telefono, ciudad, direccion, cedula, etc.) en CUALQUIER mensaje anterior, NO lo pidas de nuevo. Usa la informacion que ya tienes. Si necesitas confirmar un dato, hazlo UNA sola vez.

REGLA CRITICA - NO RE-SALUDAR
Si el cliente YA fue saludado o YA dio su nombre en mensajes anteriores, NO vuelvas a saludar como si fuera la primera vez. Si el cliente vuelve despues de horas o dias, di algo como "Hola de nuevo [nombre], que bueno que vuelves" y retoma el tema pendiente. NO repitas el flujo de bienvenida.

TODOS LOS PRODUCTOS:
{product_info}

FLUJO DE CONVERSACION
1. Si no tienes el nombre Y es la primera interaccion, saluda y pregunta nombre.
2. Si YA tienes el nombre, NO vuelvas a saludar. Continua la conversacion donde se quedo.
3. Cuando identifiques el producto de interes, incluye: [UPDATE_LEAD:product_interest=NombreProducto]
4. Si el cliente YA tiene un producto asignado pero pregunta por otro diferente, responde sobre el nuevo producto y actualiza con [UPDATE_LEAD:product_interest=NuevoProducto].

DETECCION DE PRODUCTO - MUY IMPORTANTE
Tu objetivo principal es identificar que producto le interesa al cliente.
Cuando el cliente mencione o muestre interes en un producto especifico, incluye:
[UPDATE_LEAD:product_interest=NombreExactoDelProducto]
Esto activara el bot especializado en ese producto para las siguientes interacciones.

COMO RESPONDER
Evita: "Gracias por su consulta", "Procedo a brindarle la informacion"
Usa: "Claro, te cuento", "Buena pregunta", "Mira, te explico rapido"

RESPUESTAS CORTAS: entre 1 y {max_lines} lineas.

PROHIBIDO
{prohibited}
- NO uses markdown, negritas, asteriscos ni formatos especiales. Solo texto plano.
- Si piden hablar con un humano, responde que un asesor se comunicara pronto.
- NUNCA repitas una pregunta que ya fue respondida en la conversacion.
{kb_text}

EXTRACCION AUTOMATICA DE DATOS
Al final de CADA respuesta, incluye en lineas separadas:
- Si detectas nombre: [LEAD_NAME:Nombre Apellido]
- Si detectas ciudad: [UPDATE_LEAD:city=Ciudad]
- Si detectas email: [UPDATE_LEAD:email=correo@ejemplo.com]
- Si detectas producto de interes: [UPDATE_LEAD:product_interest=NombreProducto]
- Clasifica la etapa:
  [STAGE:nuevo] - Primer contacto
  [STAGE:interesado] - Pregunta por productos, precios o beneficios
  [STAGE:en_negociacion] - Solicita compra, pago, envio, cotizacion
  [STAGE:cliente_nuevo] - Confirma compra
  [STAGE:perdido] - Rechaza explicitamente
Incluye SIEMPRE [STAGE:] al final."""

    llm_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(api_key=llm_key, session_id=session_id, system_message=system_msg)
    chat.with_model("openai", "gpt-5.2")

    for msg in history:
        if msg["role"] == "user":
            chat.messages.append({"role": "user", "content": msg["content"]})
        else:
            chat.messages.append({"role": "assistant", "content": msg["content"]})

    try:
        response = await chat.send_message(UserMessage(text=message_text))
        reply = response if isinstance(response, str) else str(response)
    except Exception as e:
        logger.error(f"WhatsApp GPT error: {e}")
        reply = "Hola! Bienvenido a Fakulti Laboratorios. Soy tu asesor virtual. En que puedo ayudarte?"

    # Parse lead name
    name_match = re.search(r'\[LEAD_NAME:([^\]]+)\]', reply)
    if name_match and not lead_name:
        detected_name = name_match.group(1).strip()
        await db.leads.update_one({"id": lead_id}, {"$set": {"name": detected_name, "last_interaction": datetime.now(timezone.utc).isoformat()}})
        await db.chat_sessions_meta.update_one({"session_id": session_id}, {"$set": {"lead_name": detected_name}}, upsert=True)
        logger.info(f"WhatsApp lead name detected: {detected_name} for {phone}")
    reply = re.sub(r'\[LEAD_NAME:[^\]]+\]', '', reply)

    # Parse lead data updates
    update_matches = re.findall(r'\[UPDATE_LEAD:(\w+)=([^\]]+)\]', reply)
    if update_matches:
        update_fields = {}
        allowed_fields = {"city", "product_interest", "email", "ci_ruc", "address"}
        for field, value in update_matches:
            if field in allowed_fields:
                update_fields[field] = value.strip()
        if update_fields:
            update_fields["last_interaction"] = datetime.now(timezone.utc).isoformat()
            await db.leads.update_one({"id": lead_id}, {"$set": update_fields})
            logger.info(f"WhatsApp lead {lead_id} updated: {update_fields}")
    reply = re.sub(r'\[UPDATE_LEAD:\w+=[^\]]+\]', '', reply)

    # Parse stage
    stage_match = re.search(r'\[STAGE:(\w+)\]', reply)
    if stage_match:
        new_stage = stage_match.group(1).strip()
        if new_stage in FUNNEL_STAGES:
            current_stage = existing_lead.get("funnel_stage", "nuevo")
            current_priority = FUNNEL_STAGES.index(current_stage) if current_stage in FUNNEL_STAGES else 0
            new_priority = FUNNEL_STAGES.index(new_stage)
            if new_stage == "perdido" or new_priority > current_priority:
                update_data = {"funnel_stage": new_stage, "last_interaction": datetime.now(timezone.utc).isoformat()}
                if new_stage in ("en_negociacion", "cliente_nuevo") and not existing_lead.get("assigned_advisor"):
                    update_data["needs_advisor"] = True
                    existing_hot_notif = await db.advisor_notifications.find_one(
                        {"lead_id": lead_id, "type": "hot_lead", "read": False}, {"_id": 0}
                    )
                    if not existing_hot_notif:
                        lead_name_for_notif = existing_lead.get("name", phone)
                        product_for_notif = existing_lead.get("product_interest", "")
                        stage_label = "quiere comprar" if new_stage == "cliente_nuevo" else "en negociacion"
                        await db.advisor_notifications.insert_one({
                            "id": str(uuid.uuid4()), "advisor_id": "admin", "type": "hot_lead",
                            "title": f"Lead caliente: {lead_name_for_notif} ({stage_label})",
                            "message": f"{lead_name_for_notif} esta listo para compra{f' de {product_for_notif}' if product_for_notif else ''}. Asigna un asesor para cerrar la venta.",
                            "lead_id": lead_id, "session_id": session_id, "read": False,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
                        logger.info(f"Hot lead notification: {lead_name_for_notif} reached {new_stage}")
                await db.leads.update_one({"id": lead_id}, {"$set": update_data})
    reply = re.sub(r'\[STAGE:\w+\]', '', reply).strip()

    # Handover detection
    msg_lower = message_text.strip().lower()
    user_wants_handover = any(kw in msg_lower for kw in HANDOVER_KEYWORDS)
    reply_lower = reply.lower()
    bot_wants_handover = any(phrase in reply_lower for phrase in BOT_TRANSFER_PHRASES)
    needs_handover = user_wants_handover or bot_wants_handover
    handover_reason = "solicitud_usuario" if user_wants_handover else ("bot_transfer" if bot_wants_handover else None)

    if needs_handover and lead_id:
        await db.leads.update_one(
            {"id": lead_id},
            {"$set": {"needs_advisor": True, "last_interaction": datetime.now(timezone.utc).isoformat()}}
        )
        existing_alert = await db.handover_alerts.find_one({"lead_id": lead_id, "status": "pending"}, {"_id": 0})
        if not existing_alert:
            lead_doc = await db.leads.find_one({"id": lead_id}, {"_id": 0, "name": 1, "whatsapp": 1, "product_interest": 1, "channel": 1, "funnel_stage": 1})
            lead_name_alert = (lead_doc.get("name", "") if lead_doc else "") or phone
            product_alert = (lead_doc.get("product_interest", "") if lead_doc else "")
            alert_message = message_text[:150] if user_wants_handover else f"Bot transfirio: {reply[:120]}"
            await db.handover_alerts.insert_one({
                "id": str(uuid.uuid4()), "lead_id": lead_id, "lead_name": lead_name_alert,
                "lead_phone": phone, "message": alert_message, "reason": handover_reason,
                "product": product_alert, "channel": (lead_doc.get("channel", "") if lead_doc else ""),
                "status": "pending", "created_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Handover alert created for {lead_name_alert} ({phone}) - reason: {handover_reason}")
        existing_notif = await db.advisor_notifications.find_one(
            {"lead_id": lead_id, "type": "advisor_request", "read": False}, {"_id": 0}
        )
        if not existing_notif:
            lead_doc_n = await db.leads.find_one({"id": lead_id}, {"_id": 0, "name": 1, "product_interest": 1})
            lead_name_notif = (lead_doc_n.get("name", "") if lead_doc_n else "") or phone
            product_notif = (lead_doc_n.get("product_interest", "") if lead_doc_n else "")
            reason_label = "El cliente solicito un asesor" if user_wants_handover else "El bot transfirio al cliente"
            await db.advisor_notifications.insert_one({
                "id": str(uuid.uuid4()), "advisor_id": "admin", "type": "advisor_request",
                "title": f"Solicitud de asesor: {lead_name_notif}",
                "message": f"{reason_label}{f' para {product_notif}' if product_notif else ''}. Requiere atencion inmediata.",
                "lead_id": lead_id, "session_id": session_id, "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Advisor request notification for {lead_name_notif} (reason: {handover_reason})")

    await db.leads.update_one({"id": lead_id}, {"$set": {"last_interaction": datetime.now(timezone.utc).isoformat()}})
    return reply, lead_id


@router.get("/webhook/whatsapp")
async def whatsapp_verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    config = await get_whatsapp_config()
    valid_token = config.get("verify_token", "") or os.environ.get("VERIFY_TOKEN", "")
    if mode == "subscribe" and token and token == valid_token:
        logger.info("WhatsApp webhook verified successfully")
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/whatsapp")
async def whatsapp_incoming(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}

    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            if value.get("statuses"):
                continue
            messages = value.get("messages", [])
            for msg in messages:
                phone = normalize_phone_ec(msg.get("from", ""))
                msg_type = msg.get("type", "")

                if msg_type == "text":
                    text = msg.get("text", {}).get("body", "")
                elif msg_type == "image":
                    text = msg.get("image", {}).get("caption", "") or "[El cliente envio una imagen]"
                elif msg_type == "audio":
                    text = "[El cliente envio un audio]"
                elif msg_type == "video":
                    text = msg.get("video", {}).get("caption", "") or "[El cliente envio un video]"
                elif msg_type == "document":
                    text = f"[El cliente envio un documento: {msg.get('document', {}).get('filename', 'archivo')}]"
                elif msg_type == "sticker":
                    text = "[El cliente envio un sticker]"
                elif msg_type == "location":
                    loc = msg.get("location", {})
                    text = f"[Ubicacion: {loc.get('latitude', '')}, {loc.get('longitude', '')}]"
                elif msg_type == "contacts":
                    text = "[El cliente compartio un contacto]"
                elif msg_type == "reaction":
                    continue
                else:
                    text = f"[Mensaje tipo: {msg_type}]"

                if phone and text:
                        logger.info(f"WhatsApp incoming from {phone}: {text[:50]}...")
                        start_time = datetime.now(timezone.utc)
                        reply, lead_id = await process_whatsapp_incoming(phone, text)
                        response_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                        sent = await send_whatsapp_message(phone, reply)
                        session_id = f"wa_{phone}"
                        now = datetime.now(timezone.utc).isoformat()
                        updated_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0, "name": 1}) if lead_id else None
                        resolved_lead_name = (updated_lead.get("name", "") if updated_lead else "") or phone
                        await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "session_id": session_id, "lead_id": lead_id, "role": "user", "content": text, "timestamp": now, "source": "whatsapp"})
                        await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "session_id": session_id, "lead_id": lead_id, "role": "assistant", "content": reply, "timestamp": now, "source": "whatsapp", "response_time_ms": response_time_ms, "delivered": sent})
                        await db.chat_sessions_meta.update_one(
                            {"session_id": session_id},
                            {"$set": {"session_id": session_id, "lead_id": lead_id, "lead_name": resolved_lead_name, "source": "whatsapp", "last_activity": now}},
                            upsert=True
                        )
                        # Bot timeout detection
                        if lead_id:
                            recent_msgs = await db.chat_messages.find(
                                {"session_id": session_id, "role": "user"}, {"_id": 0, "timestamp": 1}
                            ).sort("timestamp", -1).to_list(5)
                            if len(recent_msgs) >= 3:
                                first_msg_time = recent_msgs[-1].get("timestamp", "")
                                if first_msg_time:
                                    try:
                                        first_dt = datetime.fromisoformat(first_msg_time.replace("Z", "+00:00"))
                                        now_dt = datetime.now(timezone.utc)
                                        elapsed = (now_dt - first_dt).total_seconds()
                                        if elapsed > BOT_TIMEOUT_SECONDS:
                                            lead_check = await db.leads.find_one({"id": lead_id}, {"_id": 0, "funnel_stage": 1})
                                            if lead_check and lead_check.get("funnel_stage") == "nuevo":
                                                existing_timeout_alert = await db.handover_alerts.find_one({"lead_id": lead_id, "status": "pending"}, {"_id": 0})
                                                if not existing_timeout_alert:
                                                    lead_doc_t = await db.leads.find_one({"id": lead_id}, {"_id": 0, "name": 1, "whatsapp": 1, "product_interest": 1, "channel": 1})
                                                    await db.handover_alerts.insert_one({
                                                        "id": str(uuid.uuid4()), "lead_id": lead_id,
                                                        "lead_name": (lead_doc_t.get("name", "") if lead_doc_t else "") or phone,
                                                        "lead_phone": phone, "message": text, "reason": "timeout_bot",
                                                        "product": (lead_doc_t.get("product_interest", "") if lead_doc_t else ""),
                                                        "channel": (lead_doc_t.get("channel", "") if lead_doc_t else ""),
                                                        "status": "pending", "created_at": datetime.now(timezone.utc).isoformat()
                                                    })
                                                    await db.leads.update_one({"id": lead_id}, {"$set": {"needs_advisor": True}})
                                                    logger.info(f"Timeout handover alert for {phone}")
                                    except Exception:
                                        pass

                        # Notify assigned advisor
                        if lead_id:
                            lead_check_advisor = await db.leads.find_one({"id": lead_id}, {"_id": 0, "assigned_advisor": 1, "name": 1})
                            if lead_check_advisor and lead_check_advisor.get("assigned_advisor"):
                                existing_notif = await db.advisor_notifications.find_one(
                                    {"lead_id": lead_id, "advisor_id": lead_check_advisor["assigned_advisor"], "read": False}, {"_id": 0}
                                )
                                if not existing_notif:
                                    await db.advisor_notifications.insert_one({
                                        "id": str(uuid.uuid4()),
                                        "advisor_id": lead_check_advisor["assigned_advisor"],
                                        "lead_id": lead_id, "lead_name": lead_check_advisor.get("name", ""),
                                        "lead_phone": phone, "message": text[:100],
                                        "type": "new_message", "read": False,
                                        "created_at": datetime.now(timezone.utc).isoformat()
                                    })
    return {"status": "ok"}


@router.post("/whatsapp/webhook")
async def whatsapp_webhook_legacy(req: WhatsAppMessage):
    phone = normalize_phone_ec(req.from_number.strip())
    session_id = f"wa_{phone}"
    now = datetime.now(timezone.utc).isoformat()

    await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "session_id": session_id, "lead_id": None, "role": "user", "content": req.message, "timestamp": now, "source": "whatsapp"})

    reply, lead_id = await process_whatsapp_incoming(phone, req.message)

    await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "session_id": session_id, "lead_id": lead_id, "role": "assistant", "content": reply, "timestamp": now, "source": "whatsapp"})

    updated_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0, "name": 1}) if lead_id else None
    resolved_name = (updated_lead.get("name", "") if updated_lead else "") or phone
    await db.chat_sessions_meta.update_one(
        {"session_id": session_id},
        {"$set": {"session_id": session_id, "lead_id": lead_id, "lead_name": resolved_name, "source": "whatsapp", "last_activity": now}},
        upsert=True
    )
    if lead_id:
        await db.chat_messages.update_one({"session_id": session_id, "role": "user", "lead_id": None}, {"$set": {"lead_id": lead_id}})

    return {"reply": reply, "lead_id": lead_id}


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), user=Depends(get_current_user)):
    content = await file.read()
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/api/uploads/{filename}", "filename": filename}


@router.get("/uploads/{filename}")
async def serve_upload(filename: str):
    filepath = UPLOAD_DIR / filename
    if not filepath.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(filepath)
