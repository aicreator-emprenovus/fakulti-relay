from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import httpx
import os
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("relay")

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "fakulti-whatsapp-verify-token")
BACKEND_URL = os.environ.get("BACKEND_URL", "https://gamified-sales-flow.preview.emergentagent.com")

@app.get("/api/webhook/whatsapp")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info(f"Webhook verified OK")
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/api/webhook/whatsapp")
async def receive(request: Request):
    body = await request.json()
    logger.info(f"Incoming message, forwarding to backend")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{BACKEND_URL}/api/webhook/whatsapp", json=body, timeout=30)
            logger.info(f"Backend responded: {resp.status_code}")
        except Exception as e:
            logger.error(f"Forward error: {e}")
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok", "relay": True}
