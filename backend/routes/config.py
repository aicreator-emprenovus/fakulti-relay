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


@router.get("/config/whatsapp/diagnose")
async def diagnose_wa(user=Depends(get_current_user)):
    """Diagnóstico completo de la integración WhatsApp Cloud API."""
    config = await get_whatsapp_config()
    checks = []

    phone_id = config.get("phone_number_id", "")
    token = config.get("access_token", "")
    verify_token = config.get("verify_token", "")

    checks.append({
        "name": "Credenciales cargadas",
        "ok": bool(phone_id and token),
        "detail": f"phone_number_id={'OK' if phone_id else 'VACÍO'} | access_token={'OK' if token else 'VACÍO'} | verify_token={'OK' if verify_token else 'VACÍO'}"
    })

    if not (phone_id and token):
        return {"checks": checks, "summary": "Faltan credenciales. Guarda phone_number_id y access_token en el panel."}

    headers = {"Authorization": f"Bearer {token}"}
    phone_info = None
    waba_id = None

    # Check 1: Número válido en Meta
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{WHATSAPP_API_URL}/{phone_id}?fields=display_phone_number,verified_name,quality_rating,code_verification_status,name_status,platform_type", headers=headers, timeout=10)
            if r.status_code == 200:
                phone_info = r.json()
                checks.append({
                    "name": "Número reconocido por Meta",
                    "ok": True,
                    "detail": f"display={phone_info.get('display_phone_number')} | verified_name={phone_info.get('verified_name')} | quality={phone_info.get('quality_rating')} | status={phone_info.get('code_verification_status')} | platform={phone_info.get('platform_type')}"
                })
            else:
                checks.append({
                    "name": "Número reconocido por Meta",
                    "ok": False,
                    "detail": f"HTTP {r.status_code} - {r.text[:300]}"
                })
                return {"checks": checks, "summary": "El phone_number_id o el access_token son inválidos / no coinciden con la misma WABA."}
    except Exception as e:
        checks.append({"name": "Número reconocido por Meta", "ok": False, "detail": str(e)})
        return {"checks": checks, "summary": "Error de red al consultar Meta."}

    # Check 2: WABA del número (para poder consultar subscribed_apps)
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{WHATSAPP_API_URL}/{phone_id}?fields=whatsapp_business_account", headers=headers, timeout=10)
            if r.status_code == 200:
                waba_id = (r.json().get("whatsapp_business_account") or {}).get("id")
    except Exception:
        pass

    # Check 3: Webhook subscription en la WABA
    if waba_id:
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{WHATSAPP_API_URL}/{waba_id}/subscribed_apps", headers=headers, timeout=10)
                if r.status_code == 200:
                    apps = r.json().get("data", [])
                    if apps:
                        names = [a.get("whatsapp_business_api_data", {}).get("name") or a.get("id") for a in apps]
                        checks.append({"name": "Webhook subscrito en la WABA", "ok": True, "detail": f"Apps: {names}"})
                    else:
                        checks.append({"name": "Webhook subscrito en la WABA", "ok": False, "detail": "Ninguna app subscrita. Falta suscribir tu app al WABA desde Meta."})
                else:
                    checks.append({"name": "Webhook subscrito en la WABA", "ok": False, "detail": f"HTTP {r.status_code} - {r.text[:200]}"})
        except Exception as e:
            checks.append({"name": "Webhook subscrito en la WABA", "ok": False, "detail": str(e)})
    else:
        checks.append({"name": "Webhook subscrito en la WABA", "ok": False, "detail": "No se pudo obtener WABA ID (el token quizá no tiene permiso whatsapp_business_management)."})

    # Check 4: Registro Cloud API
    if phone_info and phone_info.get("platform_type") and phone_info.get("platform_type") != "CLOUD_API":
        checks.append({"name": "Número en Cloud API", "ok": False, "detail": f"platform_type={phone_info.get('platform_type')} (debe ser CLOUD_API). Registra el número en Meta Business → Cloud API."})
    else:
        checks.append({"name": "Número en Cloud API", "ok": True, "detail": "platform_type=CLOUD_API"})

    # Check 5: URL pública del webhook que debe estar en Meta
    import os as _os
    public_url = _os.environ.get("REACT_APP_BACKEND_URL", "") or _os.environ.get("PUBLIC_URL", "")
    expected_webhook = f"{public_url.rstrip('/')}/api/webhook/whatsapp" if public_url else "(configura REACT_APP_BACKEND_URL)"
    checks.append({
        "name": "Webhook callback esperado en Meta",
        "ok": True,
        "detail": f"URL: {expected_webhook} | Verify Token: {verify_token}"
    })

    all_ok = all(c["ok"] for c in checks)
    summary = "Todo OK. Si aún no recibes mensajes, revisa que en Meta App Dashboard → WhatsApp → Configuration, el Callback URL y Verify Token coincidan exactamente, y que el campo 'messages' esté marcado." if all_ok else "Hay checks fallidos. Revisa el detalle de cada uno."
    return {"checks": checks, "summary": summary, "waba_id": waba_id}


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
