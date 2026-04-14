from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime, timezone
from database import db
from auth import get_current_user, safe_hash_password
from models import AdvisorCreate

router = APIRouter(prefix="/api")


@router.get("/advisors")
async def get_advisors(user=Depends(get_current_user)):
    advisors = await db.admin_users.find({"role": "advisor"}, {"_id": 0, "password_hash": 0}).to_list(100)
    for a in advisors:
        a["assigned_leads_count"] = await db.leads.count_documents({"assigned_advisor": a["id"]})
    return advisors


@router.post("/advisors")
async def create_advisor(req: AdvisorCreate, user=Depends(get_current_user)):
    if user.get("role") not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Sin permisos")
    existing = await db.admin_users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    advisor_doc = {
        "id": str(uuid.uuid4()),
        "email": req.email,
        "password_hash": safe_hash_password(req.password),
        "name": req.name,
        "role": "advisor",
        "whatsapp": req.whatsapp,
        "status": req.status,
        "specialization": req.specialization,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_users.insert_one(advisor_doc)
    advisor_doc.pop("_id", None)
    advisor_doc.pop("password_hash", None)
    return advisor_doc


@router.put("/advisors/{advisor_id}")
async def update_advisor(advisor_id: str, user=Depends(get_current_user)):
    return {"message": "Endpoint de actualizacion"}


@router.put("/advisors/{advisor_id}/status")
async def update_advisor_status(advisor_id: str, body: dict, user=Depends(get_current_user)):
    new_status = body.get("status", "")
    if not new_status:
        raise HTTPException(status_code=400, detail="status requerido")
    result = await db.admin_users.update_one(
        {"id": advisor_id, "role": "advisor"},
        {"$set": {"status": new_status}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Asesor no encontrado")
    advisor = await db.admin_users.find_one({"id": advisor_id}, {"_id": 0, "password_hash": 0})
    return advisor


@router.delete("/advisors/{advisor_id}")
async def delete_advisor(advisor_id: str, user=Depends(get_current_user)):
    if user.get("role") not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Sin permisos")
    result = await db.admin_users.delete_one({"id": advisor_id, "role": "advisor"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Asesor no encontrado")
    await db.leads.update_many({"assigned_advisor": advisor_id}, {"$set": {"assigned_advisor": ""}})
    return {"message": "Asesor eliminado"}


@router.get("/advisors/notifications")
async def get_advisor_notifications(user=Depends(get_current_user)):
    user_id = user["id"]
    role = user.get("role", "admin")
    if role in ("admin", "developer"):
        notifs = await db.advisor_notifications.find({"$or": [{"advisor_id": user_id}, {"advisor_id": "admin"}]}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    else:
        notifs = await db.advisor_notifications.find({"advisor_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return notifs


@router.put("/advisors/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, user=Depends(get_current_user)):
    await db.advisor_notifications.update_one({"id": notif_id}, {"$set": {"read": True}})
    return {"message": "Notificacion leida"}


@router.put("/advisors/notifications/read-all")
async def mark_all_notifications_read(user=Depends(get_current_user)):
    user_id = user["id"]
    role = user.get("role", "admin")
    if role in ("admin", "developer"):
        await db.advisor_notifications.update_many({"$or": [{"advisor_id": user_id}, {"advisor_id": "admin"}], "read": False}, {"$set": {"read": True}})
    else:
        await db.advisor_notifications.update_many({"advisor_id": user_id, "read": False}, {"$set": {"read": True}})
    return {"message": "Todas las notificaciones marcadas como leidas"}


@router.get("/notifications")
async def get_notifications(user=Depends(get_current_user)):
    notifs = await db.notifications.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return notifs
