from fastapi import APIRouter, Depends
from database import db
from auth import get_current_user
from utils import FUNNEL_STAGES

router = APIRouter(prefix="/api")


@router.get("/dashboard/stats")
async def get_dashboard_stats(user=Depends(get_current_user)):
    total_leads = await db.leads.count_documents({})
    stages = {}
    for stage in FUNNEL_STAGES:
        stages[stage] = await db.leads.count_documents({"funnel_stage": stage})

    total_sales = 0
    pipeline = [{"$unwind": "$purchase_history"}, {"$group": {"_id": None, "total": {"$sum": "$purchase_history.price"}, "count": {"$sum": 1}}}]
    result = await db.leads.aggregate(pipeline).to_list(1)
    if result:
        total_sales = result[0]["total"]
        total_orders = result[0]["count"]
    else:
        total_orders = 0

    clients = await db.leads.count_documents({"funnel_stage": {"$in": ["cliente_nuevo", "cliente_activo"]}})
    game_plays = await db.game_plays.count_documents({})
    game_conversions = await db.game_plays.count_documents({"converted": True})

    product_stats = await db.leads.aggregate([
        {"$unwind": "$purchase_history"},
        {"$group": {"_id": "$purchase_history.product_name", "count": {"$sum": 1}, "revenue": {"$sum": "$purchase_history.price"}}}
    ]).to_list(100)

    source_stats = await db.leads.aggregate([
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ]).to_list(100)

    recent_leads = await db.leads.find({}, {"_id": 0, "id": 1, "name": 1, "whatsapp": 1, "funnel_stage": 1, "product_interest": 1, "created_at": 1, "last_interaction": 1}).sort("created_at", -1).limit(10).to_list(10)

    return {
        "total_leads": total_leads,
        "stages": stages,
        "total_sales": round(total_sales, 2),
        "total_orders": total_orders,
        "total_clients": clients,
        "game_plays": game_plays,
        "game_conversions": game_conversions,
        "conversion_rate": round((clients / total_leads * 100) if total_leads > 0 else 0, 1),
        "product_stats": [{"name": p["_id"], "count": p["count"], "revenue": round(p["revenue"], 2)} for p in product_stats],
        "source_stats": [{"name": s["_id"] or "Sin fuente", "count": s["count"]} for s in source_stats],
        "recent_leads": recent_leads
    }


@router.get("/dashboard/advisor-stats")
async def get_advisor_dashboard_stats(user=Depends(get_current_user)):
    advisors = await db.admin_users.find({"role": "advisor"}, {"_id": 0, "password_hash": 0}).to_list(100)
    advisor_stats = []
    for a in advisors:
        aid = a["id"]
        total_leads = await db.leads.count_documents({"assigned_advisor": aid})
        won_leads = await db.leads.count_documents({"assigned_advisor": aid, "funnel_stage": {"$in": ["cliente_nuevo", "cliente_activo"]}})
        lost_leads = await db.leads.count_documents({"assigned_advisor": aid, "funnel_stage": "perdido"})
        negotiating = await db.leads.count_documents({"assigned_advisor": aid, "funnel_stage": "en_negociacion"})

        pipeline = [
            {"$match": {"assigned_advisor": aid}},
            {"$unwind": "$purchase_history"},
            {"$group": {"_id": None, "total": {"$sum": "$purchase_history.price"}, "count": {"$sum": 1}}}
        ]
        rev = await db.leads.aggregate(pipeline).to_list(1)
        revenue = round(rev[0]["total"], 2) if rev else 0
        orders = rev[0]["count"] if rev else 0
        active_chats = await db.leads.count_documents({"assigned_advisor": aid, "bot_paused": True})
        conversion = round((won_leads / total_leads * 100) if total_leads > 0 else 0, 1)

        advisor_stats.append({
            "id": aid, "name": a.get("name", ""), "email": a.get("email", ""),
            "status": a.get("status", "desconectado"), "specialization": a.get("specialization", ""),
            "total_leads": total_leads, "won_leads": won_leads, "lost_leads": lost_leads,
            "negotiating": negotiating, "revenue": revenue, "orders": orders,
            "active_chats": active_chats, "conversion_rate": conversion
        })

    total_assigned = sum(a["total_leads"] for a in advisor_stats)
    total_unassigned = await db.leads.count_documents({"$or": [{"assigned_advisor": ""}, {"assigned_advisor": {"$exists": False}}]})
    total_revenue = sum(a["revenue"] for a in advisor_stats)

    return {
        "advisors": advisor_stats,
        "summary": {
            "total_assigned": total_assigned,
            "total_unassigned": total_unassigned,
            "total_advisors": len(advisors),
            "total_revenue_by_advisors": round(total_revenue, 2)
        }
    }
