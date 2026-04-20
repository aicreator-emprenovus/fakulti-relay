from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone, timedelta
from database import db
from auth import get_current_user

router = APIRouter(prefix="/api")


@router.get("/audit-logs")
async def list_audit_logs(
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    user_email: str = "",
    action: str = "",
    date_from: str = "",
    date_to: str = "",
):
    """Lists audit logs. Only admin and developer roles can access."""
    role = user.get("role", "admin")
    if role not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Solo administradores pueden ver el historial")

    q = {}
    if user_email:
        q["user_email"] = {"$regex": user_email, "$options": "i"}
    if action:
        q["action"] = {"$regex": action, "$options": "i"}
    if date_from or date_to:
        q["timestamp"] = {}
        if date_from:
            q["timestamp"]["$gte"] = date_from
        if date_to:
            q["timestamp"]["$lte"] = date_to

    total = await db.audit_logs.count_documents(q)
    skip = (page - 1) * page_size
    items = await db.audit_logs.find(q, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(page_size).to_list(page_size)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/audit-logs/summary")
async def audit_summary(user=Depends(get_current_user), hours: int = 24):
    """Quick summary of recent activity for the dashboard panel."""
    role = user.get("role", "admin")
    if role not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Solo administradores")
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    pipeline = [
        {"$match": {"timestamp": {"$gte": cutoff}}},
        {"$group": {"_id": {"user": "$user_email", "action": "$action"}, "count": {"$sum": 1}, "last": {"$max": "$timestamp"}}},
        {"$sort": {"last": -1}},
        {"$limit": 30},
    ]
    rows = await db.audit_logs.aggregate(pipeline).to_list(30)
    return [{"user_email": r["_id"]["user"], "action": r["_id"]["action"], "count": r["count"], "last": r["last"]} for r in rows]
