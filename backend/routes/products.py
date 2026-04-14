from fastapi import APIRouter, HTTPException, Depends
import uuid
import logging
from datetime import datetime, timezone
from database import db
from auth import get_current_user
from models import ProductCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/products")
async def get_products():
    products = await db.products.find({}, {"_id": 0}).to_list(100)
    return products


@router.get("/products/export")
async def export_products(user=Depends(get_current_user)):
    products = await db.products.find({}, {"_id": 0}).to_list(100)
    return products


@router.post("/products/import")
async def import_products(body: dict, user=Depends(get_current_user)):
    products_data = body.get("products", [])
    if not products_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron productos")
    imported = 0
    for p in products_data:
        doc = {
            "id": str(uuid.uuid4()),
            "name": p.get("name", "Producto importado"),
            "code": p.get("code", ""),
            "description": p.get("description", ""),
            "price": float(p.get("price", 0)),
            "original_price": float(p.get("original_price", 0)) if p.get("original_price") else None,
            "image_url": p.get("image_url", ""),
            "stock": int(p.get("stock", 100)),
            "category": p.get("category", "general"),
            "active": p.get("active", True) if isinstance(p.get("active"), bool) else str(p.get("active", "true")).lower() in ("true", "1", "si"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        bot_config = p.get("bot_config")
        if bot_config and isinstance(bot_config, dict):
            doc["bot_config"] = bot_config
        elif any(p.get(k) for k in ["personality", "key_benefits", "usage_info", "restrictions", "faqs", "sales_flow"]):
            doc["bot_config"] = {
                "personality": p.get("personality", ""),
                "key_benefits": p.get("key_benefits", ""),
                "usage_info": p.get("usage_info", ""),
                "restrictions": p.get("restrictions", ""),
                "faqs": p.get("faqs", ""),
                "sales_flow": p.get("sales_flow", ""),
            }
        await db.products.insert_one(doc)
        imported += 1
    return {"message": f"{imported} productos importados exitosamente", "imported": imported}


@router.delete("/products/all")
async def delete_all_products(user=Depends(get_current_user)):
    if user.get("role") not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Sin permisos")
    # Mark that products have been managed so seed data doesn't re-create them
    await db.system_config.update_one({"id": "products_managed"}, {"$set": {"id": "products_managed", "value": True}}, upsert=True)
    # Get all product names before deleting to clean lead references
    all_products = await db.products.find({}, {"_id": 0, "name": 1}).to_list(500)
    product_names = [p["name"] for p in all_products if p.get("name")]
    result = await db.products.delete_many({})
    # Clear product_interest on leads that referenced deleted products
    if product_names:
        await db.leads.update_many(
            {"product_interest": {"$in": product_names}},
            {"$set": {"product_interest": ""}}
        )
    # Remove all loyalty sequences
    await db.loyalty_sequences.delete_many({})
    await db.loyalty_enrollments.delete_many({})
    logger.info(f"All products deleted: {result.deleted_count}, lead product refs cleared")
    return {"message": f"{result.deleted_count} productos eliminados", "deleted": result.deleted_count}


@router.post("/products")
async def create_product(req: ProductCreate, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), **req.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.products.insert_one(doc)
    doc.pop("_id", None)
    await db.system_config.update_one({"id": "products_managed"}, {"$set": {"id": "products_managed", "value": True}}, upsert=True)
    return doc


@router.put("/products/{product_id}")
async def update_product(product_id: str, req: ProductCreate, user=Depends(get_current_user)):
    await db.products.update_one({"id": product_id}, {"$set": req.model_dump()})
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    return product


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, user=Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id}, {"_id": 0, "name": 1})
    await db.products.delete_one({"id": product_id})
    # Clear product_interest references in leads so bot doesn't use deleted product
    if product:
        await db.leads.update_many(
            {"product_interest": product.get("name", "")},
            {"$set": {"product_interest": ""}}
        )
    # Also remove loyalty sequences tied to this product
    await db.loyalty_sequences.delete_many({"product_id": product_id})
    return {"message": "Producto eliminado"}


@router.get("/products/{product_id}/bot-config")
async def get_product_bot_config(product_id: str, user=Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {
        "product_id": product["id"],
        "product_name": product["name"],
        "bot_config": product.get("bot_config", {"personality": "", "key_benefits": "", "usage_info": "", "restrictions": "", "faqs": ""})
    }


@router.put("/products/{product_id}/bot-config")
async def update_product_bot_config(product_id: str, config: dict, user=Depends(get_current_user)):
    await db.products.update_one(
        {"id": product_id},
        {"$set": {"bot_config": config.get("bot_config", config)}}
    )
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    return {"product_id": product_id, "product_name": product["name"], "bot_config": product.get("bot_config", {})}
