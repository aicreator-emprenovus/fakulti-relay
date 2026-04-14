from fastapi import APIRouter, Depends
import httpx
from database import db
from auth import get_current_user
from models import WhatsAppConfigUpdate, AIConfigUpdate
from whatsapp_utils import get_whatsapp_config, WHATSAPP_API_URL

router = APIRouter(prefix="/api")


@router.get("/config/whatsapp")
async def get_wa_config(user=Depends(get_current_user)):
    config = await get_whatsapp_config()
    safe = {**config}
    if safe.get("access_token"):
        safe["access_token"] = safe["access_token"][:10] + "..." + safe["access_token"][-4:] if len(safe["access_token"]) > 14 else "****"
    return safe


@router.put("/config/whatsapp")
async def update_wa_config(req: WhatsAppConfigUpdate, user=Depends(get_current_user)):
    data = req.model_dump()
    if data.get("access_token") and "..." in data["access_token"]:
        existing = await get_whatsapp_config()
        data["access_token"] = existing.get("access_token", "")
    data["id"] = "main"
    await db.whatsapp_config.update_one({"id": "main"}, {"$set": data}, upsert=True)
    config = await db.whatsapp_config.find_one({"id": "main"}, {"_id": 0})
    if config.get("access_token"):
        config["access_token"] = config["access_token"][:10] + "..." + config["access_token"][-4:] if len(config["access_token"]) > 14 else "****"
    return config


@router.post("/config/whatsapp/test")
async def test_wa_connection(user=Depends(get_current_user)):
    config = await get_whatsapp_config()
    if not config.get("phone_number_id") or not config.get("access_token"):
        return {"success": False, "message": "Credenciales no configuradas"}
    url = f"{WHATSAPP_API_URL}/{config['phone_number_id']}"
    headers = {"Authorization": f"Bearer {config['access_token']}"}
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {"success": True, "message": f"Conectado: {data.get('display_phone_number', 'OK')}", "phone": data.get("display_phone_number")}
            return {"success": False, "message": f"Error {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/config/ai")
async def get_ai_config(user=Depends(get_current_user)):
    config = await db.ai_config.find_one({"id": "main"}, {"_id": 0})
    return config or {"id": "main", "intent_analysis": True, "lead_classification": True, "product_recommendation": True, "suggested_responses": True}


@router.put("/config/ai")
async def update_ai_config(req: AIConfigUpdate, user=Depends(get_current_user)):
    data = req.model_dump()
    data["id"] = "main"
    await db.ai_config.update_one({"id": "main"}, {"$set": data}, upsert=True)
    return data
