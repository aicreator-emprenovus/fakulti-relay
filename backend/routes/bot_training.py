from fastapi import APIRouter, HTTPException, Depends
import uuid
import os
import logging
from datetime import datetime, timezone
from database import db
from auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/bot-training/global-config")
async def get_bot_global_config(user=Depends(get_current_user)):
    config = await db.bot_training.find_one({"id": "global"}, {"_id": 0})
    if not config:
        config = {
            "id": "global",
            "bot_name": "Asesor Virtual Fakulti",
            "brand_name": "Fakulti",
            "tone": "Cercano, experto, humano, confiable. Ciencia + natural = Biotecnologia.",
            "greeting_style": "Saluda con un emoji y pregunta el nombre del cliente.",
            "farewell_style": "Despidete cordialmente y recuerda que estas disponible.",
            "prohibited_phrases": "No prometer curas. No afirmar que reemplaza tratamientos medicos.",
            "general_instructions": "",
            "max_emojis_per_message": 2,
            "max_lines_per_message": 6
        }
        await db.bot_training.insert_one({**config})
    return config


@router.put("/bot-training/global-config")
async def update_bot_global_config(config: dict, user=Depends(get_current_user)):
    if user.get("role") != "developer":
        raise HTTPException(status_code=403, detail="Solo el desarrollador puede modificar la configuracion global del bot")
    config["id"] = "global"
    await db.bot_training.update_one({"id": "global"}, {"$set": config}, upsert=True)
    updated = await db.bot_training.find_one({"id": "global"}, {"_id": 0})
    return updated


@router.get("/bot-training/knowledge-base")
async def get_knowledge_base(user=Depends(get_current_user)):
    entries = await db.knowledge_base.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return entries


@router.post("/bot-training/knowledge-base")
async def add_knowledge_entry(body: dict, user=Depends(get_current_user)):
    if user.get("role") != "developer":
        raise HTTPException(status_code=403, detail="Solo el desarrollador")
    entry = {
        "id": str(uuid.uuid4()),
        "question": body.get("question", ""),
        "answer": body.get("answer", ""),
        "category": body.get("category", "general"),
        "active": body.get("active", True),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.knowledge_base.insert_one(entry)
    entry.pop("_id", None)
    return entry


@router.put("/bot-training/knowledge-base/{entry_id}")
async def update_knowledge_entry(entry_id: str, body: dict, user=Depends(get_current_user)):
    if user.get("role") != "developer":
        raise HTTPException(status_code=403, detail="Solo el desarrollador")
    update = {}
    for k in ["question", "answer", "category", "active"]:
        if k in body:
            update[k] = body[k]
    if update:
        await db.knowledge_base.update_one({"id": entry_id}, {"$set": update})
    entry = await db.knowledge_base.find_one({"id": entry_id}, {"_id": 0})
    return entry


@router.delete("/bot-training/knowledge-base/{entry_id}")
async def delete_knowledge_entry(entry_id: str, user=Depends(get_current_user)):
    if user.get("role") != "developer":
        raise HTTPException(status_code=403, detail="Solo el desarrollador")
    await db.knowledge_base.delete_one({"id": entry_id})
    return {"message": "Entrada eliminada"}


@router.get("/bot-training/export")
async def export_bot_training(user=Depends(get_current_user)):
    config = await db.bot_training.find_one({"id": "global"}, {"_id": 0})
    entries = await db.knowledge_base.find({}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return {"global_config": config or {}, "knowledge_base": entries}


@router.post("/bot-training/import")
async def import_bot_training(body: dict, user=Depends(get_current_user)):
    if user.get("role") != "developer":
        raise HTTPException(status_code=403, detail="Solo el desarrollador")
    imported_config = False
    imported_kb = 0

    gc = body.get("global_config")
    if gc and isinstance(gc, dict):
        gc["id"] = "global"
        await db.bot_training.update_one({"id": "global"}, {"$set": gc}, upsert=True)
        imported_config = True

    kb_entries = body.get("knowledge_base", [])
    for entry in kb_entries:
        doc = {
            "id": str(uuid.uuid4()),
            "question": entry.get("question", entry.get("Pregunta", "")),
            "answer": entry.get("answer", entry.get("Respuesta", "")),
            "category": entry.get("category", entry.get("Categoria", "general")),
            "active": entry.get("active", True) if isinstance(entry.get("active"), bool) else str(entry.get("active", entry.get("Activo", "true"))).lower() not in ("no", "false", "0"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if doc["question"] and doc["answer"]:
            await db.knowledge_base.insert_one(doc)
            imported_kb += 1

    parts = []
    if imported_config:
        parts.append("Config global importada")
    if imported_kb:
        parts.append(f"{imported_kb} entradas de conocimiento importadas")
    return {"message": " | ".join(parts) if parts else "Sin datos para importar", "config_imported": imported_config, "kb_imported": imported_kb}


@router.delete("/bot-training/all")
async def delete_all_bot_training(user=Depends(get_current_user)):
    if user.get("role") != "developer":
        raise HTTPException(status_code=403, detail="Solo el desarrollador")
    await db.bot_training.delete_many({})
    kb_result = await db.knowledge_base.delete_many({})
    logger.info(f"Bot training reset: config deleted, {kb_result.deleted_count} KB entries deleted")
    return {"message": f"Config del bot reseteada y {kb_result.deleted_count} entradas de conocimiento eliminadas", "kb_deleted": kb_result.deleted_count}


@router.post("/bot-training/test")
async def test_bot_response(body: dict, user=Depends(get_current_user)):
    if user.get("role") != "developer":
        raise HTTPException(status_code=403, detail="Solo el desarrollador")

    message = body.get("message", "")
    test_session_id = body.get("session_id", "test_session")
    if not message:
        raise HTTPException(status_code=400, detail="Mensaje requerido")

    products = await db.products.find({"active": True}, {"_id": 0}).to_list(100)
    product_info = "\n".join([f"- {p['name']}: ${p['price']} - {p.get('description', '')}" for p in products])

    # Use global config from Bot Training Center
    global_config = await db.bot_training.find_one({"id": "global"}, {"_id": 0}) or {}
    bot_name = global_config.get("bot_name", "Asesor Virtual Fakulti")
    brand_name = global_config.get("brand_name", "Fakulti")
    tone = global_config.get("tone", "Cercano, experto, humano, confiable.")
    greeting_style = global_config.get("greeting_style", "Saluda con un emoji.")
    farewell_style = global_config.get("farewell_style", "Despidete cordialmente.")
    prohibited = global_config.get("prohibited_phrases", "No prometer curas.")
    general_inst = global_config.get("general_instructions", "")
    max_emojis = global_config.get("max_emojis_per_message", 2)
    max_lines = global_config.get("max_lines_per_message", 6)

    kb_entries = await db.knowledge_base.find({"active": True}, {"_id": 0, "question": 1, "answer": 1}).to_list(50)
    kb_text = ""
    if kb_entries:
        kb_text = "\n\nBASE DE CONOCIMIENTO:\n" + "\n".join([f"P: {e['question']}\nR: {e['answer']}" for e in kb_entries])

    system_msg = f"""Eres {bot_name}, asesor virtual de {brand_name} por WhatsApp.
Tono: {tone}
Saludo: {greeting_style}
Despedida: {farewell_style}
Maximo {max_emojis} emojis, maximo {max_lines} lineas.
{f"INSTRUCCIONES: {general_inst}" if general_inst else ""}

PRODUCTOS:
{product_info}

PROHIBIDO:
{prohibited}
- NO uses markdown ni formatos especiales.
{kb_text}

EXTRACCION DE DATOS:
- Si detectas nombre: [LEAD_NAME:Nombre]
- Si detectas ciudad: [UPDATE_LEAD:city=Ciudad]
- Si detectas producto: [UPDATE_LEAD:product_interest=Producto]
- Etapa: [STAGE:nuevo|interesado|en_negociacion|cliente_nuevo|perdido]"""

    history = await db.chat_messages.find(
        {"session_id": test_session_id}, {"_id": 0}
    ).sort("timestamp", 1).limit(20).to_list(20)

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        chat = LlmChat(api_key=llm_key, session_id=test_session_id, system_message=system_msg)
        chat.with_model("openai", "gpt-5.2")

        for msg in history:
            if msg["role"] == "user":
                chat.messages.append({"role": "user", "content": msg["content"]})
            else:
                chat.messages.append({"role": "assistant", "content": msg["content"]})

        response = await chat.send_message(UserMessage(text=message))
        reply = response if isinstance(response, str) else str(response)
    except Exception as e:
        logger.error(f"Test bot GPT error: {e}")
        reply = f"Error de IA: {str(e)}"

    import re
    clean_reply = re.sub(r'\[LEAD_NAME:[^\]]+\]', '', reply)
    clean_reply = re.sub(r'\[UPDATE_LEAD:\w+=[^\]]+\]', '', clean_reply)
    clean_reply = re.sub(r'\[STAGE:\w+\]', '', clean_reply).strip()

    now = datetime.now(timezone.utc).isoformat()
    await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "session_id": test_session_id, "lead_id": None, "role": "user", "content": message, "timestamp": now, "source": "test_console"})
    await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "session_id": test_session_id, "lead_id": None, "role": "assistant", "content": clean_reply, "timestamp": now, "source": "test_console"})

    return {"response": clean_reply, "raw_response": reply}


@router.get("/bot-training/admins")
async def get_admin_users_for_dev(user=Depends(get_current_user)):
    if user.get("role") != "developer":
        raise HTTPException(status_code=403, detail="Solo el desarrollador")
    users = await db.admin_users.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
    return users
