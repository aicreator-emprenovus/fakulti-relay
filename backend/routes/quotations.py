from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import uuid
import io
from datetime import datetime, timezone
from database import db
from auth import get_current_user
from models import QuotationCreate

router = APIRouter(prefix="/api")


@router.get("/quotations")
async def get_quotations(user=Depends(get_current_user)):
    quotations = await db.quotations.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return quotations


@router.post("/quotations")
async def create_quotation(req: QuotationCreate, user=Depends(get_current_user)):
    lead = await db.leads.find_one({"id": req.lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    items_with_subtotal = []
    total = 0
    for item in req.items:
        subtotal = item.get("price", 0) * item.get("quantity", 1)
        items_with_subtotal.append({**item, "subtotal": subtotal})
        total += subtotal

    quotation_doc = {
        "id": str(uuid.uuid4()),
        "lead_id": req.lead_id,
        "lead_name": lead.get("name", ""),
        "lead_whatsapp": lead.get("whatsapp", ""),
        "items": items_with_subtotal,
        "total": round(total, 2),
        "notes": req.notes,
        "status": "pendiente",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.quotations.insert_one(quotation_doc)
    quotation_doc.pop("_id", None)
    return quotation_doc


@router.get("/quotations/{quotation_id}/pdf")
async def get_quotation_pdf(quotation_id: str):
    quotation = await db.quotations.find_one({"id": quotation_id}, {"_id": 0})
    if not quotation:
        raise HTTPException(status_code=404, detail="Cotizacion no encontrada")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body {{ font-family: Arial; padding: 40px; color: #333; }}
.header {{ text-align: center; border-bottom: 3px solid #1A6B3C; padding-bottom: 20px; margin-bottom: 30px; }}
.header h1 {{ color: #1A6B3C; margin: 0; font-size: 28px; }}
.header p {{ color: #666; margin: 5px 0; }}
.info {{ margin-bottom: 20px; }}
.info p {{ margin: 3px 0; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th {{ background: #1A6B3C; color: white; padding: 12px; text-align: left; }}
td {{ padding: 10px; border-bottom: 1px solid #eee; }}
.total {{ text-align: right; font-size: 20px; color: #1A6B3C; font-weight: bold; margin-top: 20px; }}
.footer {{ text-align: center; margin-top: 40px; color: #999; font-size: 12px; }}
</style></head><body>
<div class="header"><h1>FAKULTI LABORATORIOS</h1><p>Cotizacion #{quotation_id[:8]}</p><p>Fecha: {quotation['created_at'][:10]}</p></div>
<div class="info"><p><strong>Cliente:</strong> {quotation['lead_name']}</p><p><strong>WhatsApp:</strong> {quotation['lead_whatsapp']}</p></div>
<table><tr><th>#</th><th>Producto</th><th>Cantidad</th><th>P. Unitario</th><th>Subtotal</th></tr>"""

    for i, item in enumerate(quotation["items"], 1):
        html += f"<tr><td>{i}</td><td>{item.get('name', '')}</td><td>{item.get('quantity', 1)}</td><td>${item.get('price', 0):.2f}</td><td>${item.get('subtotal', 0):.2f}</td></tr>"

    html += f"""</table>
<div class="total">TOTAL: ${quotation['total']:.2f}</div>
{f"<p><strong>Notas:</strong> {quotation['notes']}</p>" if quotation.get('notes') else ""}
<div class="footer"><p>Fakulti Laboratorios - Suplementos Naturales de Alta Calidad</p><p>Esta cotizacion tiene validez de 15 dias</p></div>
</body></html>"""

    buffer = io.BytesIO(html.encode("utf-8"))
    return StreamingResponse(
        buffer,
        media_type="text/html",
        headers={"Content-Disposition": f"inline; filename=cotizacion_{quotation_id[:8]}.html"}
    )
