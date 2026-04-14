from fastapi import APIRouter, HTTPException, Depends, Query
import uuid
import random
from datetime import datetime, timezone
from database import db
from auth import get_current_user
from utils import normalize_phone_ec
from models import GameConfigCreate, GamePlayRequest

router = APIRouter(prefix="/api")


@router.get("/games/config")
async def get_games_config(user=Depends(get_current_user)):
    configs = await db.games_config.find({}, {"_id": 0}).to_list(100)
    return configs


@router.post("/games/config")
async def create_game_config(req: GameConfigCreate, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), **req.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.games_config.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/games/config/{config_id}")
async def update_game_config(config_id: str, req: GameConfigCreate, user=Depends(get_current_user)):
    await db.games_config.update_one({"id": config_id}, {"$set": req.model_dump()})
    config = await db.games_config.find_one({"id": config_id}, {"_id": 0})
    return config


@router.get("/games/public/{game_type}")
async def get_game_public(game_type: str):
    config = await db.games_config.find_one({"game_type": game_type, "active": True}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Juego no encontrado o inactivo")
    return config


@router.post("/games/play")
async def play_game(req: GamePlayRequest):
    config = await db.games_config.find_one({"game_type": req.game_type, "active": True}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Juego no disponible")

    wa_normalized = normalize_phone_ec(req.whatsapp)
    max_plays = config.get("max_plays_per_whatsapp", 1)
    plays = await db.game_plays.count_documents({"whatsapp": wa_normalized, "game_type": req.game_type})
    if plays >= max_plays:
        raise HTTPException(status_code=400, detail=f"Ya jugaste {plays} veces. Maximo permitido: {max_plays}")

    prizes = config.get("prizes", [])
    if not prizes:
        raise HTTPException(status_code=500, detail="Juego sin premios configurados")

    # Weighted random selection
    total_prob = sum(p.get("probability", 0) for p in prizes)
    r = random.uniform(0, total_prob)
    cumulative = 0
    selected = prizes[-1]
    for prize in prizes:
        cumulative += prize.get("probability", 0)
        if r <= cumulative:
            selected = prize
            break

    play_doc = {
        "id": str(uuid.uuid4()),
        "game_type": req.game_type,
        "whatsapp": wa_normalized,
        "name": req.name,
        "city": req.city,
        "prize_name": selected["name"],
        "prize_coupon": selected.get("coupon", ""),
        "prize_message": selected.get("message", ""),
        "played_at": datetime.now(timezone.utc).isoformat(),
        "converted": False
    }
    await db.game_plays.insert_one(play_doc)

    # Update or create lead
    from utils import find_lead_by_phone
    existing = await find_lead_by_phone(wa_normalized)
    if existing:
        update = {
            "game_used": req.game_type,
            "prize_obtained": selected["name"],
            "coupon_used": selected.get("coupon", ""),
            "last_interaction": datetime.now(timezone.utc).isoformat()
        }
        if not existing.get("name") and req.name:
            update["name"] = req.name
        if not existing.get("city") and req.city:
            update["city"] = req.city
        await db.leads.update_one({"id": existing["id"]}, {"$set": update})
    else:
        lead_doc = {
            "id": str(uuid.uuid4()), "name": req.name, "whatsapp": wa_normalized,
            "city": req.city, "email": "", "product_interest": "", "source": "Juego",
            "season": "", "channel": "Juego",
            "game_used": req.game_type, "prize_obtained": selected["name"],
            "funnel_stage": "interesado", "status": "activo",
            "purchase_history": [], "coupon_used": selected.get("coupon", ""),
            "recompra_date": None, "notes": f"Registro via {req.game_type}",
            "last_interaction": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.leads.insert_one(lead_doc)

    play_doc.pop("_id", None)
    return play_doc


@router.get("/games/plays")
async def get_game_plays(game_type: str = None, user=Depends(get_current_user)):
    query = {}
    if game_type:
        query["game_type"] = game_type
    plays = await db.game_plays.find(query, {"_id": 0}).sort("played_at", -1).to_list(500)
    return plays
