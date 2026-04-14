import re
from database import db

FUNNEL_STAGES = ["nuevo", "interesado", "en_negociacion", "cliente_nuevo", "cliente_activo", "perdido"]
STAGE_LABELS = {
    "nuevo": "Contacto inicial",
    "interesado": "Chat",
    "en_negociacion": "En Negociacion",
    "cliente_nuevo": "Leads ganados",
    "cliente_activo": "Cartera activa",
    "perdido": "Perdido",
}
SOURCES = ["TV", "QR", "Fibeca", "pauta_digital", "web", "referido", "otro"]
SEASONS = ["verano", "invierno", "todo_el_ano"]


def normalize_phone_ec(phone: str) -> str:
    phone = re.sub(r'[\s\-\(\)]', '', phone.strip())
    if phone.startswith('+593'):
        phone = '0' + phone[4:]
    elif phone.startswith('593') and len(phone) > 9:
        phone = '0' + phone[3:]
    return phone


def phone_to_international(phone: str) -> str:
    phone = re.sub(r'[\s\-\(\)]', '', phone.strip())
    if phone.startswith('+'):
        return phone[1:]
    if phone.startswith('0'):
        return '593' + phone[1:]
    if phone.startswith('593'):
        return phone
    return '593' + phone


def phone_variants(phone: str) -> list:
    normalized = normalize_phone_ec(phone)
    international = phone_to_international(phone)
    variants = list(set([normalized, international, phone.strip()]))
    return variants


async def find_lead_by_phone(phone: str):
    variants = phone_variants(phone)
    lead = await db.leads.find_one({"whatsapp": {"$in": variants}}, {"_id": 0})
    return lead
