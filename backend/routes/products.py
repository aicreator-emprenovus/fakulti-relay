from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime, timezone
from database import db
from auth import get_current_user
from models import ProductCreate

router = APIRouter(prefix="/api")


@router.get("/products")
async def get_products():
    products = await db.products.find({}, {"_id": 0}).to_list(100)
    return products


@router.post("/products")
async def create_product(req: ProductCreate, user=Depends(get_current_user)):
    doc = {"id": str(uuid.uuid4()), **req.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.products.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/products/{product_id}")
async def update_product(product_id: str, req: ProductCreate, user=Depends(get_current_user)):
    await db.products.update_one({"id": product_id}, {"$set": req.model_dump()})
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    return product


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, user=Depends(get_current_user)):
    await db.products.delete_one({"id": product_id})
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
