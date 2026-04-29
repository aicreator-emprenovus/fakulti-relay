from pydantic import BaseModel, Field
from typing import List, Optional


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
    season: Optional[str] = ""
    channel: Optional[str] = ""

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
    season: Optional[str] = None
    channel: Optional[str] = None
    assigned_advisor: Optional[str] = None
    ci_ruc: Optional[str] = None
    address: Optional[str] = None

class AdvisorCreate(BaseModel):
    name: str
    email: str
    password: str
    whatsapp: Optional[str] = ""
    status: Optional[str] = "disponible"
    specialization: Optional[str] = ""

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

class AutomationRuleCreate(BaseModel):
    name: str
    trigger_type: str
    trigger_value: Optional[str] = ""
    action_type: str
    action_value: Optional[str] = ""
    description: Optional[str] = ""
    active: Optional[bool] = True
    wa_template_name: Optional[str] = ""
    wa_template_language: Optional[str] = "es"

class WhatsAppConfigUpdate(BaseModel):
    phone_number_id: Optional[str] = ""
    access_token: Optional[str] = ""
    verify_token: Optional[str] = "fakulti-whatsapp-verify-token"
    business_name: Optional[str] = "Fakulti Laboratorios"
    catalog_id: Optional[str] = ""

class AIConfigUpdate(BaseModel):
    intent_analysis: Optional[bool] = True
    lead_classification: Optional[bool] = True
    product_recommendation: Optional[bool] = True
    suggested_responses: Optional[bool] = True

class CRMWhatsAppReply(BaseModel):
    lead_id: str
    message: str

class QRCampaignCreate(BaseModel):
    name: str
    channel: str
    source: str
    product: Optional[str] = ""
    initial_message: str
    description: Optional[str] = ""
    active: Optional[bool] = True

class PasswordResetRequest(BaseModel):
    email: str

class ResetPasswordAction(BaseModel):
    new_password: str

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    campaign_type: Optional[str] = "promo"
    target_stage: Optional[str] = ""
    target_product: Optional[str] = ""
    target_channel: Optional[str] = ""
    target_season: Optional[str] = ""
    message_template: str
    image_url: Optional[str] = ""
    scheduled_date: Optional[str] = ""
    active: Optional[bool] = True
    wa_template_name: Optional[str] = ""
    wa_template_language: Optional[str] = "es"

class ReminderCreate(BaseModel):
    name: str
    message_template: Optional[str] = ""
    target_stage: Optional[str] = ""
    target_product: Optional[str] = ""
    days_since_last_interaction: Optional[int] = 7
    batch_size: Optional[int] = 10
    active: Optional[bool] = True
    wa_template_name: Optional[str] = ""
    wa_template_language: Optional[str] = "es"

class WhatsAppMessage(BaseModel):
    from_number: str
    message: str
