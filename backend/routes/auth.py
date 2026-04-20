from fastapi import APIRouter, HTTPException, Depends, Request
import uuid
import secrets
from datetime import datetime, timezone
from database import db
from auth import (
    get_current_user, create_token, safe_hash_password,
    safe_verify_password, validate_strong_password
)
from models import LoginRequest, RegisterRequest, PasswordResetRequest, ResetPasswordAction
from audit import log_event

router = APIRouter(prefix="/api")


@router.post("/auth/login")
async def login(req: LoginRequest, request: Request):
    user = await db.admin_users.find_one({"email": req.email}, {"_id": 0})
    if not user or not safe_verify_password(req.password, user["password_hash"]):
        # Log failed attempt (anónimo pero con email intentado en details)
        ip = (request.client.host if request.client else "") or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        await log_event(
            action="Intento de login fallido",
            user=None,
            details=f"email intentado: {req.email}",
            ip=ip, path="/api/auth/login", method="POST", status=401,
            user_agent=request.headers.get("user-agent", "")
        )
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    # Log successful login with real user info
    ip = (request.client.host if request.client else "") or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    await log_event(
        action="Inicio de sesión",
        user={"id": user["id"], "email": user["email"], "name": user.get("name", ""), "role": user.get("role", "admin")},
        details="",
        ip=ip, path="/api/auth/login", method="POST", status=200,
        user_agent=request.headers.get("user-agent", "")
    )
    token = create_token(user["id"], user["email"])
    return {
        "token": token,
        "user": {
            "id": user["id"], "email": user["email"], "name": user["name"],
            "role": user.get("role", "admin"),
            "must_change_password": user.get("must_change_password", False)
        }
    }


@router.post("/auth/register")
async def register(req: RegisterRequest):
    existing = await db.admin_users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": req.email,
        "password_hash": safe_hash_password(req.password),
        "name": req.name,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_users.insert_one(user_doc)
    token = create_token(user_doc["id"], user_doc["email"])
    return {"token": token, "user": {"id": user_doc["id"], "email": user_doc["email"], "name": user_doc["name"], "role": "admin"}}


@router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "name": user["name"], "role": user.get("role", "admin"), "must_change_password": user.get("must_change_password", False)}


@router.post("/auth/change-password")
async def change_password(body: dict, user=Depends(get_current_user)):
    new_password = body.get("new_password", "")
    current_password = body.get("current_password", "")
    if not user.get("must_change_password", False):
        if not current_password:
            raise HTTPException(status_code=400, detail="Contrasena actual requerida")
        if not safe_verify_password(current_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Contrasena actual incorrecta")
    error = validate_strong_password(new_password)
    if error:
        raise HTTPException(status_code=400, detail=error)
    await db.admin_users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": safe_hash_password(new_password), "must_change_password": False}}
    )
    return {"message": "Contrasena actualizada exitosamente"}


@router.post("/auth/generate-provisional-password")
async def generate_provisional_password(body: dict, user=Depends(get_current_user)):
    target_user_id = body.get("user_id", "")
    if not target_user_id:
        raise HTTPException(status_code=400, detail="user_id requerido")
    target = await db.admin_users.find_one({"id": target_user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    role = user.get("role", "admin")
    target_role = target.get("role", "admin")
    if role == "developer" and target_role not in ("admin", "advisor"):
        raise HTTPException(status_code=403, detail="Sin permisos")
    if role == "admin" and target_role != "advisor":
        raise HTTPException(status_code=403, detail="Solo puedes generar contrasenas para asesores")
    if role == "advisor":
        raise HTTPException(status_code=403, detail="Sin permisos")
    chars_upper = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    chars_lower = "abcdefghjkmnpqrstuvwxyz"
    chars_digits = "23456789"
    chars_special = "!@#$%&*"
    provisional = (
        secrets.choice(chars_upper) +
        secrets.choice(chars_lower) +
        secrets.choice(chars_digits) +
        secrets.choice(chars_special) +
        ''.join(secrets.choice(chars_upper + chars_lower + chars_digits + chars_special) for _ in range(6))
    )
    provisional_list = list(provisional)
    secrets.SystemRandom().shuffle(provisional_list)
    provisional = ''.join(provisional_list)
    await db.admin_users.update_one(
        {"id": target_user_id},
        {"$set": {"password_hash": safe_hash_password(provisional), "must_change_password": True}}
    )
    return {"provisional_password": provisional, "user_name": target.get("name", ""), "user_email": target.get("email", "")}


@router.post("/auth/forgot-password")
async def forgot_password(req: PasswordResetRequest):
    user = await db.admin_users.find_one({"email": req.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Email no encontrado en el sistema")
    role = user.get("role", "admin")
    if role == "admin":
        notify_role = "developer"
        display_message = "Solicitud enviada al Desarrollador del sistema. Contacta a tu desarrollador para que genere tu contrasena provisional."
    elif role == "advisor":
        notify_role = "admin"
        display_message = "Solicitud enviada al Administrador. Contacta a tu administrador para que genere tu contrasena provisional."
    else:
        raise HTTPException(status_code=400, detail="Los desarrolladores no pueden solicitar reset por esta via")
    await db.password_reset_requests.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_email": user["email"],
        "user_name": user.get("name", ""),
        "user_role": role,
        "notify_role": notify_role,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"message": display_message}


@router.get("/auth/password-reset-requests")
async def get_password_reset_requests(user=Depends(get_current_user)):
    role = user.get("role", "admin")
    if role == "developer":
        query = {"notify_role": "developer", "status": "pending"}
    elif role == "admin":
        query = {"notify_role": "admin", "status": "pending"}
    else:
        return []
    requests = await db.password_reset_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return requests


@router.post("/auth/approve-reset/{request_id}")
async def approve_password_reset(request_id: str, user=Depends(get_current_user)):
    role = user.get("role", "admin")
    reset_req = await db.password_reset_requests.find_one({"id": request_id, "status": "pending"}, {"_id": 0})
    if not reset_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if role == "developer" and reset_req["user_role"] != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos")
    if role == "admin" and reset_req["user_role"] != "advisor":
        raise HTTPException(status_code=403, detail="Sin permisos")
    reset_token = secrets.token_urlsafe(32)
    await db.password_reset_requests.update_one(
        {"id": request_id},
        {"$set": {"status": "approved", "reset_token": reset_token, "approved_by": user["id"], "approved_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": f"Solicitud aprobada. {reset_req['user_name']} podra crear su nueva contrasena desde el login."}


@router.post("/auth/check-reset")
async def check_reset_available(body: dict):
    email = body.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")
    request = await db.password_reset_requests.find_one(
        {"user_email": email, "status": "approved"},
        {"_id": 0, "id": 1, "user_name": 1}
    )
    if request:
        return {"has_approved_reset": True, "user_name": request.get("user_name", "")}
    return {"has_approved_reset": False}


@router.post("/auth/set-new-password")
async def set_new_password(body: dict):
    email = body.get("email", "")
    new_password = body.get("new_password", "")
    if not email or not new_password:
        raise HTTPException(status_code=400, detail="Email y nueva contrasena requeridos")
    error = validate_strong_password(new_password)
    if error:
        raise HTTPException(status_code=400, detail=error)
    request = await db.password_reset_requests.find_one(
        {"user_email": email, "status": "approved"}, {"_id": 0}
    )
    if not request:
        raise HTTPException(status_code=404, detail="No hay solicitud de restablecimiento aprobada para este email")
    await db.admin_users.update_one(
        {"id": request["user_id"]},
        {"$set": {"password_hash": safe_hash_password(new_password), "must_change_password": False}}
    )
    await db.password_reset_requests.update_one(
        {"id": request["id"]},
        {"$set": {"status": "resolved", "resolved_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Contrasena actualizada exitosamente. Ya puedes iniciar sesion."}


@router.post("/auth/reset-password/{request_id}")
async def execute_password_reset(request_id: str, body: ResetPasswordAction, user=Depends(get_current_user)):
    role = user.get("role", "admin")
    reset_req = await db.password_reset_requests.find_one({"id": request_id, "status": "pending"}, {"_id": 0})
    if not reset_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if role == "admin" and reset_req["user_role"] != "advisor":
        raise HTTPException(status_code=403, detail="Sin permisos")
    await db.admin_users.update_one(
        {"id": reset_req["user_id"]},
        {"$set": {"password_hash": safe_hash_password(body.new_password), "must_change_password": True}}
    )
    await db.password_reset_requests.update_one(
        {"id": request_id},
        {"$set": {"status": "resolved", "resolved_by": user["id"], "resolved_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": f"Contrasena provisional de {reset_req['user_email']} establecida. Debera cambiarla al iniciar sesion."}


@router.post("/auth/reset-password-direct")
async def direct_password_reset(body: dict, user=Depends(get_current_user)):
    role = user.get("role", "admin")
    target_user_id = body.get("user_id", "")
    new_password = body.get("new_password", "")
    if not target_user_id or not new_password:
        raise HTTPException(status_code=400, detail="user_id y new_password requeridos")
    target = await db.admin_users.find_one({"id": target_user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    target_role = target.get("role", "admin")
    if role != "admin" or target_role != "advisor":
        raise HTTPException(status_code=403, detail="Solo el admin puede resetear contrasenas de asesores")
    await db.admin_users.update_one(
        {"id": target_user_id},
        {"$set": {"password_hash": safe_hash_password(new_password), "must_change_password": True}}
    )
    return {"message": f"Contrasena provisional de {target['email']} establecida. Debera cambiarla al iniciar sesion."}
