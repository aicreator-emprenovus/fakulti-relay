import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from database import db, client
from auth import safe_hash_password
from utils import normalize_phone_ec, phone_to_international

from routes import (
    auth as auth_routes,
    dashboard as dashboard_routes,
    leads as leads_routes,
    advisors as advisors_routes,
    products as products_routes,
    bot_training as bot_training_routes,
    games as games_routes,
    quotations as quotations_routes,
    loyalty as loyalty_routes,
    chat as chat_routes,
    bulk as bulk_routes,
    whatsapp as whatsapp_routes,
    automation as automation_routes,
    config as config_routes,
    campaigns as campaigns_routes,
)
from routes.automation import process_automation_rules_background

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Include all routers
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(leads_routes.router)
app.include_router(advisors_routes.router)
app.include_router(products_routes.router)
app.include_router(bot_training_routes.router)
app.include_router(games_routes.router)
app.include_router(quotations_routes.router)
app.include_router(loyalty_routes.router)
app.include_router(chat_routes.router)
app.include_router(bulk_routes.router)
app.include_router(whatsapp_routes.router)
app.include_router(automation_routes.router)
app.include_router(config_routes.router)
app.include_router(campaigns_routes.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React static files in production
import pathlib as _pathlib
_static_dir = _pathlib.Path(__file__).parent / "static"
if _static_dir.is_dir() and (_static_dir / "index.html").is_file():
    from starlette.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    _static_assets = _static_dir / "static"
    if _static_assets.is_dir():
        app.mount("/static", StaticFiles(directory=str(_static_assets)), name="spa-static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        file_path = _static_dir / full_path
        if file_path.is_file() and ".." not in full_path:
            return FileResponse(file_path)
        return FileResponse(_static_dir / "index.html")


# ========== STARTUP - SEED DATA ==========

@app.on_event("startup")
async def startup():
    # Seed developer account
    dev_exists = await db.admin_users.find_one({"role": "developer"})
    if not dev_exists:
        try:
            dev_doc = {
                "id": str(uuid.uuid4()),
                "email": "aicreator@emprenovus.com",
                "password_hash": safe_hash_password("Jlsb*1082"),
                "name": "Desarrollador",
                "role": "developer",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.admin_users.insert_one(dev_doc)
            logger.info("Developer user seeded: aicreator@emprenovus.com")
        except Exception as e:
            logger.error(f"Failed to seed developer: {e}")

    admin_count = await db.admin_users.count_documents({"role": "admin"})
    if admin_count == 0:
        try:
            admin_doc = {
                "id": str(uuid.uuid4()),
                "email": "admin@fakulti.com",
                "password_hash": safe_hash_password("admin123"),
                "name": "Admin Fakulti",
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.admin_users.insert_one(admin_doc)
            logger.info("Admin user seeded: admin@fakulti.com")
        except Exception as e:
            logger.error(f"Failed to seed admin: {e}")

    product_count = await db.products.count_documents({})
    products_ever_managed = await db.system_config.find_one({"id": "products_managed"}, {"_id": 0})
    if product_count == 0 and not products_ever_managed:
        products = [
            {"id": str(uuid.uuid4()), "name": "Bombro - Bone Broth Hidrolizado", "code": "BOMBRO", "description": "Bone Broth Hidrolizado premium. Producto unico en Ecuador. Rico en colageno y nutrientes esenciales.", "price": 55.95, "original_price": 59.99, "image_url": "https://fakultisupplements.com/wp-content/uploads/2023/02/EDIT_BONE-BROTH-POWDER-200G_FAKULTI_2024.png", "stock": 150, "category": "nutricion", "active": True, "bot_config": {"personality": "Experto en nutricion y caldo de hueso hidrolizado.", "key_benefits": "Colageno de alta absorcion, mejora digestion, soporte articular", "usage_info": "Un sachet al dia. Diluir en agua caliente.", "restrictions": "No prometer curas. No afirmar que reemplaza tratamientos medicos.", "faqs": "Se toma un sachet al dia. Apto para toda la familia."}},
            {"id": str(uuid.uuid4()), "name": "Gomitas Melatonina", "code": "GUMMELAT", "description": "Gomitas de melatonina para un descanso natural y reparador.", "price": 13.25, "original_price": 15.99, "image_url": "https://fakultisupplements.com/wp-content/uploads/2022/10/PRODUCTOS-FAKULTI-GUMMIES-DEFENSE.png", "stock": 200, "category": "bienestar", "active": True, "bot_config": {"personality": "Asesor de bienestar y descanso.", "key_benefits": "Ayuda a conciliar el sueno de forma natural", "usage_info": "Tomar 1-2 gomitas 30 minutos antes de dormir.", "restrictions": "No prometer que cura insomnio. No reemplaza tratamiento medico.", "faqs": "Son gomitas con sabor frutal. No generan dependencia."}},
            {"id": str(uuid.uuid4()), "name": "CBD Colageno Hidrolizado", "code": "CBD-COL", "description": "Colageno hidrolizado con CBD para soporte articular y bienestar integral.", "price": 52.36, "original_price": 57.45, "image_url": "https://fakultisupplements.com/wp-content/uploads/2025/08/sachets-17.png", "stock": 100, "category": "cbd", "active": True, "bot_config": {"personality": "Especialista en bienestar integral y productos con CBD.", "key_benefits": "Soporte articular, bienestar integral, colageno para piel", "usage_info": "Un sachet al dia diluido en agua.", "restrictions": "No prometer curas. CBD no es medicina.", "faqs": "El CBD es legal en Ecuador como suplemento."}},
            {"id": str(uuid.uuid4()), "name": "Pitch Up", "code": "PITCHUP", "description": "Suplemento energetico natural para rendimiento fisico y mental.", "price": 21.84, "original_price": 24.99, "image_url": "https://fakultisupplements.com/wp-content/uploads/2022/10/PRODUCTOS-FAKULTI-EXIT-FAT.png", "stock": 120, "category": "energia", "active": True, "bot_config": {"personality": "Coach de energia y rendimiento.", "key_benefits": "Energia natural sin crash", "usage_info": "Tomar un sachet al dia.", "restrictions": "No prometer resultados deportivos especificos.", "faqs": "No contiene cafeina artificial."}},
            {"id": str(uuid.uuid4()), "name": "Magnesio Citrato", "code": "MAGCIT", "description": "Magnesio citrato de alta absorcion para soporte muscular, nervioso y cardiovascular.", "price": 18.50, "original_price": 22.99, "image_url": "https://fakultisupplements.com/wp-content/uploads/2022/10/PRODUCTOS-FAKULTI-GUMMIES-DEFENSE.png", "stock": 180, "category": "bienestar", "active": True, "bot_config": {"personality": "Asesor de salud preventiva.", "key_benefits": "Soporte muscular y nervioso, alta absorcion", "usage_info": "Un sachet al dia diluido en agua.", "restrictions": "No prometer curas. Consultar con medico si toma otros medicamentos.", "faqs": "El magnesio citrato tiene mejor absorcion que otras formas."}},
        ]
        for p in products:
            p["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.products.insert_many(products)
        logger.info("Products seeded")

    game_count = await db.games_config.count_documents({})
    if game_count == 0:
        games = [
            {"id": str(uuid.uuid4()), "game_type": "roulette", "name": "Ruleta Fakulti", "prizes": [{"name": "10% Descuento", "probability": 30, "color": "#A3E635", "coupon": "RULETA10", "message": "Ganaste un 10% de descuento"}, {"name": "Envio Gratis", "probability": 20, "color": "#3B82F6", "coupon": "ENVIOGRATIS", "message": "Ganaste envio gratis"}, {"name": "Muestra Gratis Bombro", "probability": 10, "color": "#F59E0B", "coupon": "MUESTRA", "message": "Ganaste una muestra gratis"}, {"name": "15% Descuento", "probability": 8, "color": "#8B5CF6", "coupon": "RULETA15", "message": "Ganaste un 15% de descuento"}, {"name": "2x1 Gomitas", "probability": 5, "color": "#EF4444", "coupon": "2X1GOMAS", "message": "Ganaste 2x1 en Gomitas"}, {"name": "Sigue intentando", "probability": 27, "color": "#64748B", "coupon": "", "message": "No ganaste esta vez, cupon 5%: FACULTY5"}], "active": True, "max_plays_per_whatsapp": 1, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "game_type": "slot_machine", "name": "Tragamonedas Fakulti", "prizes": [{"name": "20% Descuento", "probability": 10, "color": "#A3E635", "coupon": "SLOT20", "message": "Tres iguales! 20% descuento"}, {"name": "15% Descuento", "probability": 15, "color": "#8B5CF6", "coupon": "SLOT15", "message": "15% de descuento"}, {"name": "10% Descuento", "probability": 25, "color": "#3B82F6", "coupon": "SLOT10", "message": "10% de descuento"}, {"name": "Envio Gratis", "probability": 20, "color": "#F59E0B", "coupon": "SLOTENVIO", "message": "Ganaste envio gratis"}, {"name": "5% Descuento", "probability": 30, "color": "#64748B", "coupon": "SLOT5", "message": "5% descuento: SLOT5"}], "active": True, "max_plays_per_whatsapp": 1, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "game_type": "scratch_card", "name": "Raspadita Fakulti", "prizes": [{"name": "Descuento 25%", "probability": 5, "color": "#A3E635", "coupon": "RASPA25", "message": "25% de descuento!"}, {"name": "Descuento 15%", "probability": 15, "color": "#8B5CF6", "coupon": "RASPA15", "message": "15% de descuento"}, {"name": "Descuento 10%", "probability": 25, "color": "#3B82F6", "coupon": "RASPA10", "message": "10% de descuento"}, {"name": "Envio Gratis", "probability": 25, "color": "#F59E0B", "coupon": "RASPAENVIO", "message": "Envio gratis"}, {"name": "5% Descuento", "probability": 30, "color": "#64748B", "coupon": "RASPA5", "message": "5% descuento: RASPA5"}], "active": True, "max_plays_per_whatsapp": 1, "created_at": datetime.now(timezone.utc).isoformat()}
        ]
        await db.games_config.insert_many(games)
        logger.info("Game configs seeded")

    # Migrate old games
    old_mystery = await db.games_config.find_one({"game_type": "mystery_box"})
    if old_mystery:
        await db.games_config.delete_one({"game_type": "mystery_box"})
    old_lucky = await db.games_config.find_one({"game_type": "lucky_button"})
    if old_lucky:
        await db.games_config.delete_one({"game_type": "lucky_button"})
    if not await db.games_config.find_one({"game_type": "slot_machine"}):
        await db.games_config.insert_one({"id": str(uuid.uuid4()), "game_type": "slot_machine", "name": "Tragamonedas Fakulti", "prizes": [{"name": "20% Descuento", "probability": 10, "color": "#A3E635", "coupon": "SLOT20", "message": "20% descuento"}, {"name": "10% Descuento", "probability": 25, "color": "#3B82F6", "coupon": "SLOT10", "message": "10% descuento"}, {"name": "Envio Gratis", "probability": 20, "color": "#F59E0B", "coupon": "SLOTENVIO", "message": "Envio gratis"}, {"name": "5% Descuento", "probability": 30, "color": "#64748B", "coupon": "SLOT5", "message": "5% descuento"}], "active": True, "max_plays_per_whatsapp": 1, "created_at": datetime.now(timezone.utc).isoformat()})
    if not await db.games_config.find_one({"game_type": "scratch_card"}):
        await db.games_config.insert_one({"id": str(uuid.uuid4()), "game_type": "scratch_card", "name": "Raspadita Fakulti", "prizes": [{"name": "Descuento 25%", "probability": 5, "color": "#A3E635", "coupon": "RASPA25", "message": "25% descuento!"}, {"name": "Descuento 10%", "probability": 25, "color": "#3B82F6", "coupon": "RASPA10", "message": "10% descuento"}, {"name": "Envio Gratis", "probability": 25, "color": "#F59E0B", "coupon": "RASPAENVIO", "message": "Envio gratis"}, {"name": "5% Descuento", "probability": 30, "color": "#64748B", "coupon": "RASPA5", "message": "5% descuento"}], "active": True, "max_plays_per_whatsapp": 1, "created_at": datetime.now(timezone.utc).isoformat()})

    # Seed sample leads
    leads_count = await db.leads.count_documents({})
    if leads_count == 0:
        sample_leads = [
            {"id": str(uuid.uuid4()), "name": "Maria Garcia", "whatsapp": "0991234567", "city": "Quito", "email": "maria@email.com", "product_interest": "Bombro", "source": "TV", "season": "", "channel": "TV", "funnel_stage": "cliente_activo", "status": "activo", "game_used": "roulette", "prize_obtained": "10% Descuento", "purchase_history": [{"id": str(uuid.uuid4()), "product_name": "Bombro - Bone Broth Hidrolizado", "quantity": 2, "price": 111.90, "date": "2025-12-15"}], "coupon_used": "RULETA10", "recompra_date": "2026-01-15", "notes": "Cliente frecuente"},
            {"id": str(uuid.uuid4()), "name": "Carlos Lopez", "whatsapp": "0987654321", "city": "Guayaquil", "email": "carlos@email.com", "product_interest": "Colageno CBD", "source": "QR", "season": "", "channel": "QR", "funnel_stage": "interesado", "status": "activo", "game_used": "mystery_box", "prize_obtained": "Envio Gratis", "purchase_history": [], "coupon_used": None, "recompra_date": None, "notes": "Interesado en CBD"},
            {"id": str(uuid.uuid4()), "name": "Ana Martinez", "whatsapp": "0976543210", "city": "Cuenca", "email": "ana@email.com", "product_interest": "Gomitas Melatonina", "source": "Fibeca", "season": "", "channel": "Fibeca", "funnel_stage": "cliente_nuevo", "status": "activo", "game_used": None, "prize_obtained": None, "purchase_history": [{"id": str(uuid.uuid4()), "product_name": "Gomitas Melatonina", "quantity": 1, "price": 13.25, "date": "2026-01-20"}], "coupon_used": None, "recompra_date": "2026-02-20", "notes": "Compro en Fibeca"},
            {"id": str(uuid.uuid4()), "name": "Pedro Sanchez", "whatsapp": "0965432109", "city": "Quito", "email": "", "product_interest": "Pitch Up", "source": "pauta_digital", "season": "", "channel": "pauta_digital", "funnel_stage": "en_negociacion", "status": "activo", "game_used": None, "prize_obtained": None, "purchase_history": [], "coupon_used": None, "recompra_date": None, "notes": "Pidio cotizacion"},
            {"id": str(uuid.uuid4()), "name": "Laura Fernandez", "whatsapp": "0954321098", "city": "Guayaquil", "email": "laura@email.com", "product_interest": "Bombro", "source": "TV", "season": "", "channel": "TV", "funnel_stage": "nuevo", "status": "activo", "game_used": None, "prize_obtained": None, "purchase_history": [], "coupon_used": None, "recompra_date": None, "notes": ""},
            {"id": str(uuid.uuid4()), "name": "Roberto Diaz", "whatsapp": "0943210987", "city": "Ambato", "email": "", "product_interest": "", "source": "web", "season": "", "channel": "web", "funnel_stage": "perdido", "status": "inactivo", "game_used": "slot_machine", "prize_obtained": "5% Descuento", "purchase_history": [], "coupon_used": None, "recompra_date": None, "notes": "Sin respuesta despues de 3 recordatorios"},
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

    # Seed automation rules
    rules_count = await db.automation_rules.count_documents({})
    if rules_count == 0:
        default_rules = [
            {"id": str(uuid.uuid4()), "name": "Bienvenida automatica", "trigger_type": "nuevo_lead", "trigger_value": "", "action_type": "respuesta_ia", "action_value": "Saluda al cliente con: Hola! Gracias por contactarnos. Soy el asesor virtual de Fakulti Laboratorios.", "description": "Saluda automaticamente a cada nuevo lead.", "active": True, "order": 1},
            {"id": str(uuid.uuid4()), "name": "Solicitar datos del cliente", "trigger_type": "lead_sin_datos", "trigger_value": "nombre,whatsapp,ciudad", "action_type": "respuesta_ia", "action_value": "Pregunta de forma natural los datos faltantes.", "description": "Solicita datos faltantes.", "active": True, "order": 2},
            {"id": str(uuid.uuid4()), "name": "Clasificar etapa automaticamente", "trigger_type": "analisis_conversacion", "trigger_value": "", "action_type": "cambiar_etapa", "action_value": "Analiza keywords para clasificar etapa", "description": "Clasifica automaticamente la etapa del lead.", "active": True, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Primer recordatorio (4 horas)", "trigger_type": "sin_respuesta", "trigger_value": "4", "action_type": "enviar_mensaje", "action_value": "Hola, solo para saber si pudiste revisar la informacion que te envie.", "description": "Recordatorio a las 4 horas.", "active": True, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Segundo recordatorio (24 horas)", "trigger_type": "sin_respuesta", "trigger_value": "24", "action_type": "enviar_mensaje", "action_value": "Hola de nuevo, queria saber si aun tienes interes en los productos de Fakulti.", "description": "Recordatorio a las 24 horas.", "active": True, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Marcar como perdido", "trigger_type": "sin_respuesta", "trigger_value": "48", "action_type": "cambiar_etapa", "action_value": "perdido", "description": "Marca como perdido despues de 48h.", "active": True, "order": 6},
            {"id": str(uuid.uuid4()), "name": "Transferir a humano", "trigger_type": "intencion_ia", "trigger_value": "queja,problema,reclamo,hablar con persona,agente", "action_type": "asignar_agente", "action_value": "Transfiere a un asesor humano.", "description": "Detecta intenciones criticas.", "active": True, "order": 7},
            {"id": str(uuid.uuid4()), "name": "Recomendacion de producto", "trigger_type": "intencion_ia", "trigger_value": "consulta_producto,interes,salud", "action_type": "respuesta_ia", "action_value": "Recomienda productos del catalogo.", "description": "Sugiere productos.", "active": True, "order": 8},
            {"id": str(uuid.uuid4()), "name": "Seguimiento post-compra", "trigger_type": "compra_realizada", "trigger_value": "", "action_type": "iniciar_secuencia", "action_value": "Inscribe en secuencia de fidelizacion.", "description": "Inicia fidelizacion post-compra.", "active": True, "order": 9},
            {"id": str(uuid.uuid4()), "name": "Recordatorio de recompra (30 dias)", "trigger_type": "dias_post_compra", "trigger_value": "30", "action_type": "enviar_mensaje", "action_value": "Hola! Ya paso un mes desde tu ultima compra en Fakulti. Te gustaria repetir tu pedido?", "description": "Recordatorio de recompra a 30 dias.", "active": True, "order": 10},
        ]
        for r in default_rules:
            r["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.automation_rules.insert_many(default_rules)
        logger.info("Automation rules seeded (10 rules)")

    # Seed default configs
    if not await db.whatsapp_config.find_one({"id": "main"}):
        await db.whatsapp_config.insert_one({"id": "main", "phone_number_id": "", "access_token": "", "verify_token": "fakulti-whatsapp-verify-token", "business_name": "Fakulti Laboratorios"})
    if not await db.ai_config.find_one({"id": "main"}):
        await db.ai_config.insert_one({"id": "main", "intent_analysis": True, "lead_classification": True, "product_recommendation": True, "suggested_responses": True})

    # Migrate old funnel stages
    migrated_caliente = await db.leads.update_many({"funnel_stage": "caliente"}, {"$set": {"funnel_stage": "en_negociacion"}})
    migrated_frio = await db.leads.update_many({"funnel_stage": "frio"}, {"$set": {"funnel_stage": "perdido"}})
    if migrated_caliente.modified_count or migrated_frio.modified_count:
        logger.info(f"Migrated stages: caliente->en_negociacion ({migrated_caliente.modified_count}), frio->perdido ({migrated_frio.modified_count})")

    # Phone normalization & lead dedup
    all_leads = await db.leads.find({}, {"_id": 0}).to_list(10000)
    phone_groups = {}
    for lead in all_leads:
        raw_phone = lead.get("whatsapp", "")
        if not raw_phone:
            continue
        norm = normalize_phone_ec(raw_phone)
        if norm not in phone_groups:
            phone_groups[norm] = []
        phone_groups[norm].append(lead)

    merged_count = 0
    normalized_count = 0
    for norm_phone, leads_group in phone_groups.items():
        if len(leads_group) == 1:
            lead = leads_group[0]
            if lead.get("whatsapp") != norm_phone:
                old_phone = lead["whatsapp"]
                await db.leads.update_one({"id": lead["id"]}, {"$set": {"whatsapp": norm_phone}})
                old_session = f"wa_{old_phone}"
                new_session = f"wa_{norm_phone}"
                if old_session != new_session:
                    await db.chat_sessions_meta.update_many({"session_id": old_session}, {"$set": {"session_id": new_session}})
                    await db.chat_messages.update_many({"session_id": old_session}, {"$set": {"session_id": new_session}})
                normalized_count += 1
        else:
            leads_group.sort(key=lambda lead_item: (
                bool(lead_item.get("name", "").strip()),
                len(lead_item.get("purchase_history", [])),
                lead_item.get("last_interaction", ""),
            ), reverse=True)
            primary = leads_group[0]
            primary_id = primary["id"]

            for dup in leads_group[1:]:
                dup_id = dup["id"]
                dup_purchases = dup.get("purchase_history", [])
                if dup_purchases:
                    await db.leads.update_one({"id": primary_id}, {"$push": {"purchase_history": {"$each": dup_purchases}}})
                update_fields = {}
                for field in ["name", "city", "email", "product_interest", "source", "channel", "game_used", "prize_obtained", "coupon_used"]:
                    if not primary.get(field) and dup.get(field):
                        update_fields[field] = dup[field]
                if dup.get("assigned_advisor") and not primary.get("assigned_advisor"):
                    update_fields["assigned_advisor"] = dup["assigned_advisor"]
                if update_fields:
                    await db.leads.update_one({"id": primary_id}, {"$set": update_fields})

                old_sessions_for_dup = [f"wa_{dup.get('whatsapp', '')}", f"wa_{normalize_phone_ec(dup.get('whatsapp', ''))}"]
                for old_sid in old_sessions_for_dup:
                    await db.chat_messages.update_many({"lead_id": dup_id}, {"$set": {"lead_id": primary_id}})
                    await db.chat_sessions_meta.update_many({"lead_id": dup_id}, {"$set": {"lead_id": primary_id, "lead_name": primary.get("name", "")}})

                await db.leads.delete_one({"id": dup_id})
                logger.info(f"Merged duplicate lead {dup.get('name','')} into {primary.get('name','')}")

            old_phone = primary.get("whatsapp", "")
            if old_phone != norm_phone:
                await db.leads.update_one({"id": primary_id}, {"$set": {"whatsapp": norm_phone}})

            all_variants = set()
            for dup_lead in leads_group:
                p = dup_lead.get("whatsapp", "")
                all_variants.add(f"wa_{p}")
                all_variants.add(f"wa_{normalize_phone_ec(p)}")
                all_variants.add(f"wa_{phone_to_international(p)}")
            target_session = f"wa_{norm_phone}"
            for old_sid in all_variants:
                if old_sid != target_session:
                    await db.chat_sessions_meta.update_many({"session_id": old_sid}, {"$set": {"session_id": target_session, "lead_name": primary.get("name", "")}})
                    await db.chat_messages.update_many({"session_id": old_sid}, {"$set": {"session_id": target_session, "lead_id": primary_id}})

            merged_count += len(leads_group) - 1

    if normalized_count or merged_count:
        logger.info(f"Phone migration: {normalized_count} normalized, {merged_count} duplicates merged")

    # Ensure fields on leads
    await db.leads.update_many({"season": {"$exists": False}}, {"$set": {"season": ""}})
    await db.leads.update_many({"channel": {"$exists": False}}, {"$set": {"channel": ""}})

    # Games standby
    await db.games_config.update_many({"game_type": {"$in": ["roulette", "scratch_card"]}}, {"$set": {"active": False}})

    # Seed QR campaigns
    qr_count = await db.qr_campaigns.count_documents({})
    if qr_count == 0:
        default_qr_campaigns = [
            {"id": str(uuid.uuid4()), "name": "TV - Anuncio General", "channel": "TV/QR", "source": "TV", "product": "", "initial_message": "Hola, vi esto en TV", "description": "QR para TV.", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "name": "Fibeca - Punto de Venta", "channel": "Fibeca", "source": "Fibeca", "product": "", "initial_message": "Hola, los vi en Fibeca", "description": "QR para Fibeca.", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "name": "Evento - Feria de Salud", "channel": "Evento", "source": "Evento", "product": "Bombro", "initial_message": "Hola, los conoci en la feria", "description": "QR para ferias.", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        await db.qr_campaigns.insert_many(default_qr_campaigns)
        logger.info("Default QR campaigns seeded")

    await db.qr_campaigns.update_many({"scan_count": {"$exists": False}}, {"$set": {"scan_count": 0}})
    await db.leads.update_many({"bot_paused": {"$exists": False}}, {"$set": {"bot_paused": False}})
    await db.leads.update_many({"assigned_advisor": {"$exists": False}}, {"$set": {"assigned_advisor": ""}})

    # Ensure bot_config on products
    products_without_bot = await db.products.find({"bot_config": {"$exists": False}}, {"_id": 0, "id": 1, "name": 1, "description": 1}).to_list(100)
    for p in products_without_bot:
        default_bot = {
            "personality": f"Especialista en {p.get('name', 'el producto')}.",
            "key_benefits": p.get("description", ""),
            "usage_info": "Consultar indicaciones del producto.",
            "restrictions": "No hacer promesas medicas.",
            "faqs": ""
        }
        await db.products.update_one({"id": p["id"]}, {"$set": {"bot_config": default_bot}})

    # Migration: Update Bombro with full bot_config if it has the old minimal one
    bombro = await db.products.find_one({"name": {"$regex": "Bombro|Bone Broth", "$options": "i"}}, {"_id": 0, "id": 1, "bot_config": 1})
    if bombro:
        current_personality = (bombro.get("bot_config") or {}).get("personality", "")
        current_sales_flow = (bombro.get("bot_config") or {}).get("sales_flow", "")
        if not current_sales_flow or len(current_personality) < 80:
            full_bombro_config = {
                "personality": "Asesor humano de Fakulti Laboratorios, especializado en Bone Broth Hidrolizado (Bombro). Experto en nutricion, colageno y bienestar integral. Cercano, confiable, cientifico pero accesible.",
                "key_benefits": "Colageno de alta absorcion tipo I, II y III. Mejora digestion y salud intestinal. Soporte articular y oseo. Fortalece cabello, unas y piel. Rico en aminoacidos esenciales. Producto unico en Ecuador. Biotecnologia avanzada.",
                "usage_info": "Un sachet al dia. Diluir en agua caliente o fria. Se puede mezclar con jugos o batidos. Apto para toda la familia. Sabor neutro.",
                "restrictions": "No prometer curas. No afirmar que reemplaza tratamientos medicos. No dar dosificaciones medicas. Siempre recomendar consultar con un profesional de salud.",
                "faqs": "Se toma un sachet al dia. Apto para toda la familia. No contiene azucar anadida. Es libre de gluten. Se puede tomar frio o caliente. Resultados visibles en 2-4 semanas de uso continuo.",
                "sales_flow": "MODO HUMANO AMIGABLE\nEstilo: habla como un amigo que sabe mucho de salud. Nada de frases genericas de vendedor.\n\nPASO 1 - PRIMER CONTACTO\nSi es nuevo: Hola! Bienvenido a Fakulti. Soy tu asesor de bienestar. Como te llamas?\nSi ya tiene nombre: Hola [nombre]! Que gusto saludarte. En que te puedo ayudar?\n\nPASO 2 - IDENTIFICAR NECESIDAD\nCuando el cliente mencione interes en Bombro o caldo de hueso:\n- Que bueno que te interesa Bombro! Es nuestro producto estrella.\n- Es un Bone Broth Hidrolizado premium, unico en Ecuador.\n- Tiene colageno tipo I, II y III de alta absorcion.\n- Perfecto para articulaciones, digestion, piel y cabello.\n- Un sachet al dia es todo lo que necesitas.\n\nPASO 3 - RESOLVER DUDAS\nResponde preguntas sobre:\n- Precio: $55.95 (oferta) / precio normal $59.99\n- Presentacion: Caja con sachets individuales\n- Sabor: Neutro, se mezcla facil con agua, jugos o batidos\n- Beneficios: colageno, articulaciones, digestion, piel, cabello, unas\n- Uso: 1 sachet diario, frio o caliente\n\nPASO 4 - CIERRE DE VENTA\nCuando el cliente muestre interes en comprar:\n1. Pregunta: Cuantas cajas te gustaria llevar? Tenemos promo de 2 cajas.\n2. Pide datos de envio: nombre completo, ciudad, direccion\n3. Pregunta: El pago prefieres realizar por deposito, transferencia o con tarjeta de credito?\n4. Confirma el pedido con todos los datos\n\nPASO 5 - POST-VENTA\nUna vez confirmado:\n- Perfecto! Tu pedido esta registrado.\n- Te enviaremos la confirmacion por este medio.\n- Cualquier duda, aqui estamos para ayudarte.\n\nREGLAS ESPECIALES:\n- Si pide hablar con un humano: Un momento, te transfiero con un asesor del equipo.\n- Si pregunta por otro producto: Claro, tambien tenemos otros productos. Te cuento sobre ellos.\n- Maximo 4-6 lineas por mensaje. No enviar bloques largos.\n- El cliente esta en Ecuador. Todos los precios en dolares."
            }
            await db.products.update_one({"id": bombro["id"]}, {"$set": {"bot_config": full_bombro_config}})
            logger.info("Bombro bot_config migrated to full version")

    # Migration: Seed behavior rules if none exist
    behavior_count = await db.automation_rules.count_documents({"trigger_type": "comportamiento_bot"})
    if behavior_count == 0:
        behavior_rules = [
            {"id": str(uuid.uuid4()), "name": "Formas de pago", "trigger_type": "comportamiento_bot", "trigger_value": "", "action_type": "instruccion_bot", "action_value": "Cuando el cliente pregunte por formas de pago o como pagar, responde: El pago prefieres realizar por deposito, transferencia o con tarjeta de credito? NO menciones otras formas de pago.", "description": "Define las formas de pago que el bot debe ofrecer", "active": True, "order": 100, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "name": "Tono y estilo de comunicacion", "trigger_type": "comportamiento_bot", "trigger_value": "", "action_type": "instruccion_bot", "action_value": "Habla como persona real, cercano y profesional. Frases cortas. Maximo 2 emojis por mensaje. Maximo 4-6 lineas. Evita frases como Gracias por su consulta o Procedo a brindarle informacion. Usa: Claro te cuento, Buena pregunta, Mira te explico rapido.", "description": "Define el tono y estilo del bot", "active": True, "order": 101, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "name": "Restricciones medicas", "trigger_type": "comportamiento_bot", "trigger_value": "", "action_type": "instruccion_bot", "action_value": "No prometer curas. No afirmar que los productos reemplazan tratamientos medicos. No usar markdown ni negritas, solo texto plano.", "description": "Restricciones que el bot debe seguir siempre", "active": True, "order": 102, "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        await db.automation_rules.insert_many(behavior_rules)
        logger.info("Bot behavior rules seeded (3 rules)")

    logger.info("Fakulti CRM Backend ready")

    # Start background automation scheduler
    asyncio.create_task(process_automation_rules_background())
    logger.info("Automation scheduler started (runs every 30 minutes)")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
