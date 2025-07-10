from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from app.whatsapp import WhatsAppAPI
import os
import requests

# Load environment variables
load_dotenv()

ACCESS_TOKEN = os.getenv("WA_TOKEN")
PHONE_NUMBER_ID = os.getenv("WA_PHONE_ID")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

if not ACCESS_TOKEN or not PHONE_NUMBER_ID or not RECAPTCHA_SECRET_KEY:
    raise Exception("Missing environment variables")

whatsapp_client = WhatsAppAPI(ACCESS_TOKEN, PHONE_NUMBER_ID)
app = FastAPI()

origins = [
    "http://localhost:8080",   # Vite default dev server
    "http://127.0.0.1:8080",   # If you open with 127.0.0.1 instead
    "http://localhost:3000",   # Optional: Next.js / React dev server
    "http://127.0.0.1:3000",
    # "*"                        # TEMPORARY wildcard (remove in production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use ["*"] only for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models for WhatsApp template structure
class Language(BaseModel):
    code: str

class Parameter(BaseModel):
    type: str
    text: str

class Component(BaseModel):
    type: str
    parameters: list[Parameter]

class Template(BaseModel):
    name: str
    language: Language
    components: list[Component]

class WhatsAppTemplateMessage(BaseModel):
    messaging_product: str
    to: str
    type: str
    template: Template
    captchaToken: str

# Google reCAPTCHA validation
def verify_recaptcha(token: str) -> bool:
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": RECAPTCHA_SECRET_KEY,
        "response": token
    }
    try:
        response = requests.post(url, data=data)
        result = response.json()
        return result.get("success", False) and result.get("score", 0) >= 0.5
    except Exception:
        return False

@app.post("/send")
def send_template_message(message: WhatsAppTemplateMessage, request: Request):
    if not verify_recaptcha(message.captchaToken):
        raise HTTPException(status_code=403, detail="Failed reCAPTCHA verification.")

    payload = {
        "messaging_product": "whatsapp",
        "to": message.to,
        "type": "template",
        "template": {
            "name": message.template.name,
            "language": {"code": message.template.language.code},
            "components": [
                {
                    "type": c.type,
                    "parameters": [{"type": p.type, "text": p.text} for p in c.parameters]
                } for c in message.template.components
            ]
        }
    }

    result = whatsapp_client.send_custom_payload(payload)

    if "error" in result:
        # Choose appropriate status code based on error type
        code = result.get("status_code", 500)
        error_msg = result.get("message", "Erro desconhecido ao enviar mensagem.")
        raise HTTPException(status_code=code, detail={"error": error_msg, "details": result.get("details", {})})

    return {"status": "sent", "response": result}

