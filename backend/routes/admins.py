"""Admin user CRUD — creates, edits, deletes other admin users.
The seed admin (admin@fakulti.com) is protected: it cannot be deleted nor have
its password reset by other admins."""
from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime, timezone
from database import db
from auth import get_current_user, safe_hash_password
from models import AdminCreate

router = APIRouter(prefix="/api")

PROTECTED_ADMIN_EMAIL = "admin@fakulti.com"


def _ensure_admin(user):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")


@router.get("/admins")
async def list_admins(user=Depends(get_current_user)):
    _ensure_admin(user)
    admins = await db.admin_users.find({"role": "admin"}, {"_id": 0, "password_hash": 0}).to_list(100)
    for a in admins:
        a["is_protected"] = a.get("email") == PROTECTED_ADMIN_EMAIL
    return admins


@router.post("/admins")
async def create_admin(req: AdminCreate, user=Depends(get_current_user)):
    _ensure_admin(user)
    existing = await db.admin_users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    doc = {
        "id": str(uuid.uuid4()),
        "email": req.email,
        "password_hash": safe_hash_password(req.password),
        "name": req.name,
        "role": "admin",
        "whatsapp": req.whatsapp,
        "status": req.status,
        "specialization": req.specialization,
        "must_change_password": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.admin_users.insert_one(doc)
    doc.pop("_id", None)
    doc.pop("password_hash", None)
    return doc


@router.put("/admins/{admin_id}")
async def update_admin(admin_id: str, body: dict, user=Depends(get_current_user)):
    _ensure_admin(user)
    target = await db.admin_users.find_one({"id": admin_id, "role": "admin"}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    if target.get("email") == PROTECTED_ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail=f"El usuario principal {PROTECTED_ADMIN_EMAIL} no puede ser modificado")
    allowed = {"name", "whatsapp", "status", "specialization"}
    update_fields = {k: v for k, v in (body or {}).items() if k in allowed}
    if not update_fields:
        raise HTTPException(status_code=400, detail="Nada para actualizar")
    await db.admin_users.update_one({"id": admin_id}, {"$set": update_fields})
    updated = await db.admin_users.find_one({"id": admin_id}, {"_id": 0, "password_hash": 0})
    return updated


@router.delete("/admins/{admin_id}")
async def delete_admin(admin_id: str, user=Depends(get_current_user)):
    _ensure_admin(user)
    target = await db.admin_users.find_one({"id": admin_id, "role": "admin"}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    if target.get("email") == PROTECTED_ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail=f"El usuario principal {PROTECTED_ADMIN_EMAIL} no puede ser eliminado")
    if target.get("id") == user.get("id"):
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")
    await db.admin_users.delete_one({"id": admin_id, "role": "admin"})
    return {"message": "Administrador eliminado", "name": target.get("name", "")}
