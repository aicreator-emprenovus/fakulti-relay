from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query, Header
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import io
import json
import random
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

JWT_SECRET = os.environ.get('JWT_SECRET', 'faculty-crm-jwt-secret-2024')
JWT_ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FUNNEL_STAGES = ["nuevo", "interesado", "caliente", "cliente_nuevo", "cliente_activo", "frio"]
SOURCES = ["TV", "QR", "Fibeca", "pauta_digital", "web", "referido", "otro"]

# ========== PYDANTIC MODELS ==========

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LeadCreate(BaseModel):
    name: str
    whatsapp: str
    city: Optional[str] = ""
    email: Optional[str] = ""
    product_interest: Optional[str] = ""
    source: Optional[str] = "web"
    notes: Optional[str] = ""
    funnel_stage: Optional[str] = "nuevo"

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    whatsapp: Optional[str] = None
    city: Optional[str] = None
    email: Optional[str] = None
    product_interest: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    funnel_stage: Optional[str] = None
    status: Optional[str] = None
    recompra_date: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    code: Optional[str] = ""
    description: Optional[str] = ""
    price: float
    original_price: Optional[float] = None
    image_url: Optional[str] = ""
    stock: Optional[int] = 100
    category: Optional[str] = "general"
    active: Optional[bool] = True

class GameConfigCreate(BaseModel):
    game_type: str
    name: str
    prizes: List[dict]
    active: Optional[bool] = True
    max_plays_per_whatsapp: Optional[int] = 1

class GamePlayRequest(BaseModel):
    game_type: str
    whatsapp: str
    name: str
    city: Optional[str] = ""

class QuotationCreate(BaseModel):
    lead_id: str
    items: List[dict]
    notes: Optional[str] = ""

class LoyaltySequenceCreate(BaseModel):
    product_id: str
    product_name: str
    messages: List[dict]
    active: Optional[bool] = True

class ChatMessageRequest(BaseModel):
    lead_id: Optional[str] = None
    session_id: str
    message: str

class PurchaseAdd(BaseModel):
    product_id: str
    product_name: str
    quantity: int = 1
    price: float

# ========== AUTH UTILITIES ==========

def create_token(user_id: str, email: str):
    payload = {"user_id": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(hours=24)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.admin_users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalido")

# ========== AUTH ROUTES ==========

@api_router.post("/auth/login")
async def login(req: LoginRequest):
    user = await db.admin_users.find_one({"email": req.email}, {"_id": 0})
    if not user or not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = create_token(user["id"], user["email"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"]}}

@api_router.post("/auth/register")
async def register(req: RegisterRequest):
    existing = await db.admin_users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": req.email,
        "password_hash": pwd_context.hash(req.password),
        "name": req.name,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_users.insert_one(user_doc)
    token = create_token(user_doc["id"], user_doc["email"])
    return {"token": token, "user": {"id": user_doc["id"], "email": user_doc["email"], "name": user_doc["name"]}}

@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "name": user["name"]}

# ========== DASHBOARD ROUTES ==========

@api_router.get("/dashboard/stats")
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
    
    recent_leads = await db.leads.find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    
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

# ========== LEAD ROUTES ==========

@api_router.get("/leads")
async def get_leads(
    stage: Optional[str] = None,
    search: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    user=Depends(get_current_user)
):
    query = {}
    if stage:
        query["funnel_stage"] = stage
    if source:
        query["source"] = source
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"whatsapp": {"$regex": search, "$options": "i"}},
            {"city": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.leads.count_documents(query)
    skip = (page - 1) * limit
    leads = await db.leads.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"leads": leads, "total": total, "page": page, "pages": (total + limit - 1) // limit}

@api_router.get("/leads/{lead_id}")
async def get_lead(lead_id: str, user=Depends(get_current_user)):
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    return lead

@api_router.post("/leads")
async def create_lead(req: LeadCreate, user=Depends(get_current_user)):
    lead_doc = {
        "id": str(uuid.uuid4()),
        **req.model_dump(),
        "status": "activo",
        "game_used": None,
        "prize_obtained": None,
        "purchase_history": [],
        "coupon_used": None,
        "recompra_date": None,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.leads.insert_one(lead_doc)
    lead_doc.pop("_id", None)
    return lead_doc

@api_router.put("/leads/{lead_id}")
async def update_lead(lead_id: str, req: LeadUpdate, user=Depends(get_current_user)):
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    update_data["last_interaction"] = datetime.now(timezone.utc).isoformat()
    await db.leads.update_one({"id": lead_id}, {"$set": update_data})
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    return lead

@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, user=Depends(get_current_user)):
    result = await db.leads.delete_one({"id": lead_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    return {"message": "Lead eliminado"}

@api_router.post("/leads/{lead_id}/purchase")
async def add_purchase(lead_id: str, req: PurchaseAdd, user=Depends(get_current_user)):
    purchase = {
        "id": str(uuid.uuid4()),
        "product_id": req.product_id,
        "product_name": req.product_name,
        "quantity": req.quantity,
        "price": req.price * req.quantity,
        "date": datetime.now(timezone.utc).isoformat()
    }
    await db.leads.update_one(
        {"id": lead_id},
        {
            "$push": {"purchase_history": purchase},
            "$set": {
                "funnel_stage": "cliente_nuevo",
                "last_interaction": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    return lead

@api_router.put("/leads/{lead_id}/stage")
async def update_lead_stage(lead_id: str, stage: str = Query(...)):
    if stage not in FUNNEL_STAGES:
        raise HTTPException(status_code=400, detail="Etapa invalida")
    await db.leads.update_one({"id": lead_id}, {"$set": {"funnel_stage": stage, "last_interaction": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Etapa actualizada"}

# ========== PRODUCT ROUTES ==========

@api_router.get("/products")
async def get_products():
    products = await db.products.find({}, {"_id": 0}).to_list(100)
    return products

@api_router.post("/products")
async def create_product(req: ProductCreate, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), **req.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.products.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.put("/products/{product_id}")
async def update_product(product_id: str, req: ProductCreate, user=Depends(get_current_user)):
    await db.products.update_one({"id": product_id}, {"$set": req.model_dump()})
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    return product

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, user=Depends(get_current_user)):
    await db.products.delete_one({"id": product_id})
    return {"message": "Producto eliminado"}

# ========== GAME ROUTES ==========

@api_router.get("/games/config")
async def get_games_config(user=Depends(get_current_user)):
    configs = await db.games_config.find({}, {"_id": 0}).to_list(100)
    return configs

@api_router.post("/games/config")
async def create_game_config(req: GameConfigCreate, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), **req.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.games_config.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.put("/games/config/{config_id}")
async def update_game_config(config_id: str, req: GameConfigCreate, user=Depends(get_current_user)):
    await db.games_config.update_one({"id": config_id}, {"$set": req.model_dump()})
    config = await db.games_config.find_one({"id": config_id}, {"_id": 0})
    return config

@api_router.get("/games/public/{game_type}")
async def get_game_public(game_type: str):
    config = await db.games_config.find_one({"game_type": game_type, "active": True}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Juego no disponible")
    safe_config = {"game_type": config["game_type"], "name": config["name"], "prizes": [{"name": p["name"], "color": p.get("color", "#A3E635")} for p in config["prizes"]]}
    return safe_config

@api_router.post("/games/play")
async def play_game(req: GamePlayRequest):
    config = await db.games_config.find_one({"game_type": req.game_type, "active": True}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Juego no disponible")
    
    max_plays = config.get("max_plays_per_whatsapp", 1)
    plays_count = await db.game_plays.count_documents({"whatsapp": req.whatsapp, "game_type": req.game_type})
    if plays_count >= max_plays:
        raise HTTPException(status_code=400, detail="Ya has jugado el maximo permitido")
    
    prizes = config["prizes"]
    weights = [p.get("probability", 1) for p in prizes]
    total_weight = sum(weights)
    normalized = [w / total_weight for w in weights]
    selected_prize = random.choices(prizes, weights=normalized, k=1)[0]
    
    play_doc = {
        "id": str(uuid.uuid4()),
        "whatsapp": req.whatsapp,
        "name": req.name,
        "game_type": req.game_type,
        "prize": selected_prize["name"],
        "prize_data": selected_prize,
        "converted": False,
        "played_at": datetime.now(timezone.utc).isoformat()
    }
    await db.game_plays.insert_one(play_doc)
    
    existing_lead = await db.leads.find_one({"whatsapp": req.whatsapp})
    if existing_lead:
        await db.leads.update_one(
            {"whatsapp": req.whatsapp},
            {"$set": {"game_used": req.game_type, "prize_obtained": selected_prize["name"], "last_interaction": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        lead_doc = {
            "id": str(uuid.uuid4()),
            "name": req.name,
            "whatsapp": req.whatsapp,
            "city": req.city or "",
            "email": "",
            "product_interest": "",
            "source": "QR",
            "game_used": req.game_type,
            "prize_obtained": selected_prize["name"],
            "funnel_stage": "interesado",
            "status": "activo",
            "purchase_history": [],
            "coupon_used": None,
            "recompra_date": None,
            "notes": f"Registro via juego {req.game_type}",
            "last_interaction": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.leads.insert_one(lead_doc)
    
    prize_index = prizes.index(selected_prize)
    return {"prize": selected_prize["name"], "prize_index": prize_index, "coupon": selected_prize.get("coupon", ""), "message": selected_prize.get("message", f"Ganaste: {selected_prize['name']}")}

@api_router.get("/games/plays")
async def get_game_plays(game_type: Optional[str] = None, user=Depends(get_current_user)):
    query = {}
    if game_type:
        query["game_type"] = game_type
    plays = await db.game_plays.find(query, {"_id": 0}).sort("played_at", -1).limit(200).to_list(200)
    return plays

# ========== QUOTATION ROUTES ==========

@api_router.get("/quotations")
async def get_quotations(user=Depends(get_current_user)):
    quotations = await db.quotations.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return quotations

@api_router.post("/quotations")
async def create_quotation(req: QuotationCreate, user=Depends(get_current_user)):
    lead = await db.leads.find_one({"id": req.lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in req.items)
    tax = round(subtotal * 0.12, 2)
    total = round(subtotal + tax, 2)
    
    doc = {
        "id": str(uuid.uuid4()),
        "lead_id": req.lead_id,
        "lead_name": lead.get("name", ""),
        "lead_whatsapp": lead.get("whatsapp", ""),
        "items": req.items,
        "subtotal": round(subtotal, 2),
        "tax": tax,
        "total": total,
        "notes": req.notes,
        "status": "pendiente",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.quotations.insert_one(doc)
    doc.pop("_id", None)
    
    await db.leads.update_one(
        {"id": req.lead_id},
        {"$set": {"funnel_stage": "caliente", "last_interaction": datetime.now(timezone.utc).isoformat()}}
    )
    return doc

@api_router.get("/quotations/{quotation_id}/pdf")
async def get_quotation_pdf(quotation_id: str):
    from fpdf import FPDF
    
    quotation = await db.quotations.find_one({"id": quotation_id}, {"_id": 0})
    if not quotation:
        raise HTTPException(status_code=404, detail="Cotizacion no encontrada")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "FAKULTI LABORATORIOS", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "La Ciencia de lo Natural", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Cotizacion #{quotation_id[:8]}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Fecha: {quotation['created_at'][:10]}", ln=True)
    pdf.cell(0, 7, f"Cliente: {quotation['lead_name']}", ln=True)
    pdf.cell(0, 7, f"WhatsApp: {quotation['lead_whatsapp']}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(163, 230, 53)
    pdf.cell(80, 8, "Producto", border=1, fill=True)
    pdf.cell(25, 8, "Cant.", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Precio Unit.", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Subtotal", border=1, fill=True, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 10)
    for item in quotation["items"]:
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        pdf.cell(80, 7, item.get("name", ""), border=1)
        pdf.cell(25, 7, str(qty), border=1, align="C")
        pdf.cell(35, 7, f"${price:.2f}", border=1, align="C")
        pdf.cell(35, 7, f"${price * qty:.2f}", border=1, align="C")
        pdf.ln()
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(140, 8, "Subtotal:", align="R")
    pdf.cell(35, 8, f"${quotation['subtotal']:.2f}", align="C")
    pdf.ln()
    pdf.cell(140, 8, "IVA (12%):", align="R")
    pdf.cell(35, 8, f"${quotation['tax']:.2f}", align="C")
    pdf.ln()
    pdf.cell(140, 8, "TOTAL:", align="R")
    pdf.cell(35, 8, f"${quotation['total']:.2f}", align="C")
    
    if quotation.get("notes"):
        pdf.ln(15)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 7, f"Notas: {quotation['notes']}", ln=True)
    
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=cotizacion_{quotation_id[:8]}.pdf"})

# ========== LOYALTY ROUTES ==========

@api_router.get("/loyalty/sequences")
async def get_loyalty_sequences(user=Depends(get_current_user)):
    sequences = await db.loyalty_sequences.find({}, {"_id": 0}).to_list(100)
    return sequences

@api_router.post("/loyalty/sequences")
async def create_loyalty_sequence(req: LoyaltySequenceCreate, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), **req.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.loyalty_sequences.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.put("/loyalty/sequences/{sequence_id}")
async def update_loyalty_sequence(sequence_id: str, req: LoyaltySequenceCreate, user=Depends(get_current_user)):
    await db.loyalty_sequences.update_one({"id": sequence_id}, {"$set": req.model_dump()})
    seq = await db.loyalty_sequences.find_one({"id": sequence_id}, {"_id": 0})
    return seq

@api_router.delete("/loyalty/sequences/{sequence_id}")
async def delete_loyalty_sequence(sequence_id: str, user=Depends(get_current_user)):
    await db.loyalty_sequences.delete_one({"id": sequence_id})
    return {"message": "Secuencia eliminada"}

# ========== CHAT ROUTES ==========

@api_router.post("/chat/message")
async def send_chat_message(req: ChatMessageRequest, user=Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    products = await db.products.find({}, {"_id": 0}).to_list(100)
    product_info = "\n".join([f"- {p['name']}: ${p['price']} - {p.get('description', '')}" for p in products])
    
    system_msg = f"""Eres el Asesor Virtual Oficial de Fakulti Laboratorios (marca Faculty).
Tu funcion: Atender leads, calificar, cotizar y cerrar venta.

PRODUCTOS DISPONIBLES:
{product_info}

REGLAS:
- Nunca sonar robot. Se amigable y profesional.
- Nunca hacer promesas medicas.
- Nunca afirmar que cura enfermedades.
- Nunca recomendar reemplazar tratamiento medico.
- Bombro es Bone Broth Hidrolizado, producto unico en Ecuador.
- Responde siempre en espanol.
- Se conciso pero util.
- Si el usuario pide precio, proporciona la informacion.
- Si pide comprar, indica los pasos."""

    history = await db.chat_messages.find(
        {"session_id": req.session_id}, {"_id": 0}
    ).sort("timestamp", 1).limit(20).to_list(20)
    
    llm_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(api_key=llm_key, session_id=req.session_id, system_message=system_msg)
    chat.with_model("openai", "gpt-5.2")
    
    for msg in history:
        if msg["role"] == "user":
            chat.messages.append({"role": "user", "content": msg["content"]})
        else:
            chat.messages.append({"role": "assistant", "content": msg["content"]})
    
    user_msg_doc = {
        "id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "lead_id": req.lead_id,
        "role": "user",
        "content": req.message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(user_msg_doc)
    
    try:
        response = await chat.send_message(UserMessage(text=req.message))
        assistant_content = response if isinstance(response, str) else str(response)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        assistant_content = "Disculpa, tuve un problema tecnico. ¿Puedes repetir tu consulta?"
    
    assistant_msg_doc = {
        "id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "lead_id": req.lead_id,
        "role": "assistant",
        "content": assistant_content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(assistant_msg_doc)
    
    return {"response": assistant_content, "session_id": req.session_id}

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, user=Depends(get_current_user)):
    messages = await db.chat_messages.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)
    return messages

@api_router.get("/chat/sessions")
async def get_chat_sessions(user=Depends(get_current_user)):
    pipeline = [
        {"$group": {"_id": "$session_id", "lead_id": {"$first": "$lead_id"}, "last_message": {"$last": "$content"}, "timestamp": {"$last": "$timestamp"}, "count": {"$sum": 1}}},
        {"$sort": {"timestamp": -1}},
        {"$limit": 50}
    ]
    sessions = await db.chat_messages.aggregate(pipeline).to_list(50)
    return [{"session_id": s["_id"], "lead_id": s.get("lead_id"), "last_message": s["last_message"], "timestamp": s["timestamp"], "message_count": s["count"]} for s in sessions]

# ========== BULK ROUTES ==========

@api_router.post("/bulk/upload")
async def bulk_upload(file: UploadFile = File(...), user=Depends(get_current_user)):
    import openpyxl
    
    content = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(content))
    ws = wb.active
    
    headers = [cell.value for cell in ws[1] if cell.value]
    header_map = {}
    for i, h in enumerate(headers):
        h_lower = h.lower().strip()
        if "nombre" in h_lower or "name" in h_lower:
            header_map["name"] = i
        elif "whatsapp" in h_lower or "telefono" in h_lower or "phone" in h_lower:
            header_map["whatsapp"] = i
        elif "ciudad" in h_lower or "city" in h_lower:
            header_map["city"] = i
        elif "producto" in h_lower or "product" in h_lower:
            header_map["product_interest"] = i
        elif "fecha" in h_lower or "date" in h_lower:
            header_map["purchase_date"] = i
        elif "email" in h_lower:
            header_map["email"] = i
        elif "fuente" in h_lower or "source" in h_lower:
            header_map["source"] = i
    
    created = 0
    updated = 0
    errors = 0
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        try:
            name = str(row[header_map.get("name", 0)] or "").strip()
            whatsapp = str(row[header_map.get("whatsapp", 1)] or "").strip()
            if not name or not whatsapp:
                continue
            
            city = str(row[header_map.get("city", 2)] or "").strip() if "city" in header_map else ""
            product = str(row[header_map.get("product_interest", 3)] or "").strip() if "product_interest" in header_map else ""
            email = str(row[header_map.get("email", -1)] or "").strip() if "email" in header_map else ""
            source_val = str(row[header_map.get("source", -1)] or "").strip() if "source" in header_map else "Carga masiva"
            
            has_purchase = "purchase_date" in header_map and row[header_map["purchase_date"]]
            stage = "cliente_nuevo" if has_purchase else "nuevo"
            
            existing = await db.leads.find_one({"whatsapp": whatsapp})
            if existing:
                update_data = {"name": name, "last_interaction": datetime.now(timezone.utc).isoformat()}
                if city: update_data["city"] = city
                if product: update_data["product_interest"] = product
                if has_purchase: update_data["funnel_stage"] = stage
                await db.leads.update_one({"whatsapp": whatsapp}, {"$set": update_data})
                updated += 1
            else:
                lead_doc = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "whatsapp": whatsapp,
                    "city": city,
                    "email": email,
                    "product_interest": product,
                    "source": source_val,
                    "game_used": None,
                    "prize_obtained": None,
                    "funnel_stage": stage,
                    "status": "activo",
                    "purchase_history": [],
                    "coupon_used": None,
                    "recompra_date": None,
                    "notes": "",
                    "last_interaction": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.leads.insert_one(lead_doc)
                created += 1
        except Exception as e:
            logger.error(f"Bulk upload row error: {e}")
            errors += 1
    
    return {"created": created, "updated": updated, "errors": errors, "total_processed": created + updated + errors}

@api_router.get("/bulk/download")
async def bulk_download(
    download_type: str = Query("all"),
    stage: Optional[str] = None,
    product: Optional[str] = None,
    user=Depends(get_current_user)
):
    import openpyxl
    
    query = {}
    if download_type == "stage" and stage:
        query["funnel_stage"] = stage
    elif download_type == "product" and product:
        query["product_interest"] = {"$regex": product, "$options": "i"}
    elif download_type == "fibeca":
        query["source"] = "Fibeca"
    elif download_type == "game":
        query["game_used"] = {"$ne": None}
    elif download_type == "recompra":
        query["funnel_stage"] = {"$in": ["cliente_nuevo", "cliente_activo"]}
    
    leads = await db.leads.find(query, {"_id": 0}).to_list(10000)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leads Faculty"
    
    headers_list = ["Nombre", "WhatsApp", "Email", "Ciudad", "Producto Interes", "Fuente", "Etapa Embudo", "Estado", "Juego Usado", "Premio", "Cupon", "Ultima Interaccion", "Fecha Registro"]
    ws.append(headers_list)
    
    for lead in leads:
        ws.append([
            lead.get("name", ""),
            lead.get("whatsapp", ""),
            lead.get("email", ""),
            lead.get("city", ""),
            lead.get("product_interest", ""),
            lead.get("source", ""),
            lead.get("funnel_stage", ""),
            lead.get("status", ""),
            lead.get("game_used", ""),
            lead.get("prize_obtained", ""),
            lead.get("coupon_used", ""),
            lead.get("last_interaction", ""),
            lead.get("created_at", "")
        ])
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    filename = f"leads_faculty_{download_type}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={filename}"})

# ========== HUMAN AGENT DERIVATION ==========

@api_router.post("/leads/{lead_id}/derive-human")
async def derive_to_human(lead_id: str, reason: str = Query("general"), user=Depends(get_current_user)):
    await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"status": "gestion_humana", "notes": f"Derivado a agente humano: {reason}", "last_interaction": datetime.now(timezone.utc).isoformat()}}
    )
    notification = {
        "id": str(uuid.uuid4()),
        "type": "derivacion_humana",
        "lead_id": lead_id,
        "reason": reason,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    return {"message": "Lead derivado a agente humano"}

@api_router.get("/notifications")
async def get_notifications(user=Depends(get_current_user)):
    notifs = await db.notifications.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return notifs

# ========== INCLUDE ROUTER & MIDDLEWARE ==========

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== STARTUP - SEED DATA ==========

@app.on_event("startup")
async def startup():
    admin_count = await db.admin_users.count_documents({})
    if admin_count == 0:
        admin_doc = {
            "id": str(uuid.uuid4()),
            "email": "admin@faculty.com",
            "password_hash": pwd_context.hash("admin123"),
            "name": "Admin Faculty",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.admin_users.insert_one(admin_doc)
        logger.info("Admin user seeded: admin@faculty.com / admin123")
    
    product_count = await db.products.count_documents({})
    if product_count == 0:
        products = [
            {"id": str(uuid.uuid4()), "name": "Bombro - Bone Broth Hidrolizado", "code": "BOMBRO", "description": "Bone Broth Hidrolizado premium. Producto unico en Ecuador. Rico en colageno y nutrientes esenciales.", "price": 55.95, "original_price": 59.99, "image_url": "https://fakultisupplements.com/wp-content/uploads/2023/02/EDIT_BONE-BROTH-POWDER-200G_FAKULTI_2024.png", "stock": 150, "category": "nutricion", "active": True},
            {"id": str(uuid.uuid4()), "name": "Gomitas Melatonina", "code": "GUMMELAT", "description": "Gomitas de melatonina para un descanso natural y reparador.", "price": 13.25, "original_price": 15.99, "image_url": "https://fakultisupplements.com/wp-content/uploads/2022/10/PRODUCTOS-FAKULTI-GUMMIES-DEFENSE.png", "stock": 200, "category": "bienestar", "active": True},
            {"id": str(uuid.uuid4()), "name": "CBD Colageno Hidrolizado", "code": "CBD-COL", "description": "Colageno hidrolizado con CBD para soporte articular y bienestar integral.", "price": 52.36, "original_price": 57.45, "image_url": "https://fakultisupplements.com/wp-content/uploads/2025/08/sachets-17.png", "stock": 100, "category": "cbd", "active": True},
            {"id": str(uuid.uuid4()), "name": "Pitch Up", "code": "PITCHUP", "description": "Suplemento energetico natural para rendimiento fisico y mental.", "price": 21.84, "original_price": 24.99, "image_url": "https://fakultisupplements.com/wp-content/uploads/2022/10/PRODUCTOS-FAKULTI-EXIT-FAT.png", "stock": 120, "category": "energia", "active": True},
        ]
        for p in products:
            p["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.products.insert_many(products)
        logger.info("Products seeded")
    
    game_count = await db.games_config.count_documents({})
    if game_count == 0:
        games = [
            {
                "id": str(uuid.uuid4()),
                "game_type": "roulette",
                "name": "Ruleta Faculty",
                "prizes": [
                    {"name": "10% Descuento", "probability": 30, "color": "#A3E635", "coupon": "RULETA10", "message": "Ganaste un 10% de descuento en tu proxima compra"},
                    {"name": "Envio Gratis", "probability": 20, "color": "#3B82F6", "coupon": "ENVIOGRATIS", "message": "Ganaste envio gratis en tu proxima compra"},
                    {"name": "Muestra Gratis Bombro", "probability": 10, "color": "#F59E0B", "coupon": "MUESTRA", "message": "Ganaste una muestra gratis de Bombro"},
                    {"name": "15% Descuento", "probability": 8, "color": "#8B5CF6", "coupon": "RULETA15", "message": "Ganaste un 15% de descuento"},
                    {"name": "2x1 Gomitas", "probability": 5, "color": "#EF4444", "coupon": "2X1GOMAS", "message": "Ganaste 2x1 en Gomitas Melatonina"},
                    {"name": "Sigue intentando", "probability": 27, "color": "#64748B", "coupon": "", "message": "No ganaste esta vez, pero tienes un cupon de 5%: FACULTY5"}
                ],
                "active": True,
                "max_plays_per_whatsapp": 1,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "game_type": "slot_machine",
                "name": "Tragamonedas Faculty",
                "prizes": [
                    {"name": "20% Descuento", "probability": 10, "color": "#A3E635", "coupon": "SLOT20", "message": "Tres iguales! Ganaste un 20% de descuento"},
                    {"name": "15% Descuento", "probability": 15, "color": "#8B5CF6", "coupon": "SLOT15", "message": "Gran combinacion! 15% de descuento para ti"},
                    {"name": "10% Descuento", "probability": 25, "color": "#3B82F6", "coupon": "SLOT10", "message": "Buena jugada! 10% de descuento"},
                    {"name": "Envio Gratis", "probability": 20, "color": "#F59E0B", "coupon": "SLOTENVIO", "message": "Ganaste envio gratis en tu proxima compra"},
                    {"name": "5% Descuento", "probability": 30, "color": "#64748B", "coupon": "SLOT5", "message": "Tienes un 5% de descuento: SLOT5"}
                ],
                "active": True,
                "max_plays_per_whatsapp": 1,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "game_type": "scratch_card",
                "name": "Raspadita Faculty",
                "prizes": [
                    {"name": "Descuento 25%", "probability": 5, "color": "#A3E635", "coupon": "RASPA25", "message": "Descubriste un 25% de descuento!"},
                    {"name": "Descuento 15%", "probability": 15, "color": "#8B5CF6", "coupon": "RASPA15", "message": "Debajo de la capa dorada: 15% de descuento"},
                    {"name": "Descuento 10%", "probability": 25, "color": "#3B82F6", "coupon": "RASPA10", "message": "Raspa y gana! 10% de descuento"},
                    {"name": "Envio Gratis", "probability": 25, "color": "#F59E0B", "coupon": "RASPAENVIO", "message": "Encontraste envio gratis"},
                    {"name": "5% Descuento", "probability": 30, "color": "#64748B", "coupon": "RASPA5", "message": "Un 5% de descuento te espera: RASPA5"}
                ],
                "active": True,
                "max_plays_per_whatsapp": 1,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        await db.games_config.insert_many(games)
        logger.info("Game configs seeded")
    
    # Migrate old games to new ones
    old_mystery = await db.games_config.find_one({"game_type": "mystery_box"})
    if old_mystery:
        await db.games_config.delete_one({"game_type": "mystery_box"})
        logger.info("Removed mystery_box game config")
    old_lucky = await db.games_config.find_one({"game_type": "lucky_button"})
    if old_lucky:
        await db.games_config.delete_one({"game_type": "lucky_button"})
        logger.info("Removed lucky_button game config")
    if not await db.games_config.find_one({"game_type": "slot_machine"}):
        await db.games_config.insert_one({
            "id": str(uuid.uuid4()),
            "game_type": "slot_machine",
            "name": "Tragamonedas Faculty",
            "prizes": [
                {"name": "20% Descuento", "probability": 10, "color": "#A3E635", "coupon": "SLOT20", "message": "Tres iguales! Ganaste un 20% de descuento"},
                {"name": "15% Descuento", "probability": 15, "color": "#8B5CF6", "coupon": "SLOT15", "message": "Gran combinacion! 15% de descuento para ti"},
                {"name": "10% Descuento", "probability": 25, "color": "#3B82F6", "coupon": "SLOT10", "message": "Buena jugada! 10% de descuento"},
                {"name": "Envio Gratis", "probability": 20, "color": "#F59E0B", "coupon": "SLOTENVIO", "message": "Ganaste envio gratis en tu proxima compra"},
                {"name": "5% Descuento", "probability": 30, "color": "#64748B", "coupon": "SLOT5", "message": "Tienes un 5% de descuento: SLOT5"}
            ],
            "active": True, "max_plays_per_whatsapp": 1, "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info("Slot machine game config seeded")
    if not await db.games_config.find_one({"game_type": "scratch_card"}):
        await db.games_config.insert_one({
            "id": str(uuid.uuid4()),
            "game_type": "scratch_card",
            "name": "Raspadita Faculty",
            "prizes": [
                {"name": "Descuento 25%", "probability": 5, "color": "#A3E635", "coupon": "RASPA25", "message": "Descubriste un 25% de descuento!"},
                {"name": "Descuento 15%", "probability": 15, "color": "#8B5CF6", "coupon": "RASPA15", "message": "Debajo de la capa dorada: 15% de descuento"},
                {"name": "Descuento 10%", "probability": 25, "color": "#3B82F6", "coupon": "RASPA10", "message": "Raspa y gana! 10% de descuento"},
                {"name": "Envio Gratis", "probability": 25, "color": "#F59E0B", "coupon": "RASPAENVIO", "message": "Encontraste envio gratis"},
                {"name": "5% Descuento", "probability": 30, "color": "#64748B", "coupon": "RASPA5", "message": "Un 5% de descuento te espera: RASPA5"}
            ],
            "active": True, "max_plays_per_whatsapp": 1, "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info("Scratch card game config seeded")
    
    # Seed sample leads
    leads_count = await db.leads.count_documents({})
    if leads_count == 0:
        sample_leads = [
            {"id": str(uuid.uuid4()), "name": "Maria Garcia", "whatsapp": "+593991234567", "city": "Quito", "email": "maria@email.com", "product_interest": "Bombro", "source": "TV", "funnel_stage": "cliente_activo", "status": "activo", "game_used": "roulette", "prize_obtained": "10% Descuento", "purchase_history": [{"id": str(uuid.uuid4()), "product_name": "Bombro - Bone Broth Hidrolizado", "quantity": 2, "price": 111.90, "date": "2025-12-15"}], "coupon_used": "RULETA10", "recompra_date": "2026-01-15", "notes": "Cliente frecuente"},
            {"id": str(uuid.uuid4()), "name": "Carlos Lopez", "whatsapp": "+593987654321", "city": "Guayaquil", "email": "carlos@email.com", "product_interest": "Colageno CBD", "source": "QR", "funnel_stage": "interesado", "status": "activo", "game_used": "mystery_box", "prize_obtained": "Envio Gratis", "purchase_history": [], "coupon_used": None, "recompra_date": None, "notes": "Interesado en CBD"},
            {"id": str(uuid.uuid4()), "name": "Ana Martinez", "whatsapp": "+593976543210", "city": "Cuenca", "email": "ana@email.com", "product_interest": "Gomitas Melatonina", "source": "Fibeca", "funnel_stage": "cliente_nuevo", "status": "activo", "game_used": None, "prize_obtained": None, "purchase_history": [{"id": str(uuid.uuid4()), "product_name": "Gomitas Melatonina", "quantity": 1, "price": 13.25, "date": "2026-01-20"}], "coupon_used": None, "recompra_date": "2026-02-20", "notes": "Compro en Fibeca"},
            {"id": str(uuid.uuid4()), "name": "Pedro Sanchez", "whatsapp": "+593965432109", "city": "Quito", "email": "", "product_interest": "Pitch Up", "source": "pauta_digital", "funnel_stage": "caliente", "status": "activo", "game_used": None, "prize_obtained": None, "purchase_history": [], "coupon_used": None, "recompra_date": None, "notes": "Pidio cotizacion"},
            {"id": str(uuid.uuid4()), "name": "Laura Fernandez", "whatsapp": "+593954321098", "city": "Guayaquil", "email": "laura@email.com", "product_interest": "Bombro", "source": "TV", "funnel_stage": "nuevo", "status": "activo", "game_used": None, "prize_obtained": None, "purchase_history": [], "coupon_used": None, "recompra_date": None, "notes": ""},
            {"id": str(uuid.uuid4()), "name": "Roberto Diaz", "whatsapp": "+593943210987", "city": "Ambato", "email": "", "product_interest": "", "source": "web", "funnel_stage": "frio", "status": "inactivo", "game_used": "lucky_button", "prize_obtained": "5% Descuento", "purchase_history": [], "coupon_used": None, "recompra_date": None, "notes": "Sin respuesta 48h"},
        ]
        for lead in sample_leads:
            lead["last_interaction"] = datetime.now(timezone.utc).isoformat()
            lead["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.leads.insert_many(sample_leads)
        logger.info("Sample leads seeded")

    await db.leads.create_index("whatsapp")
    await db.leads.create_index("funnel_stage")
    await db.leads.create_index("source")
    await db.game_plays.create_index("whatsapp")
    logger.info("Faculty CRM Backend ready")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
