import os
import requests
import json
from crewai.tools import tool
from twilio.rest import Client
from config import DRY_RUN

@tool("Enviar Telegram")
def send_telegram(message: str) -> str:
    """Envía mensaje a Telegram."""
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return "Error credenciales Telegram."
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
        return "Telegram enviado."
    except Exception as e: return f"Error Telegram: {e}"

@tool("Enviar Pushover")
def send_pushover(msg: str) -> str:
    """Envía notificación Pushover."""
    if DRY_RUN: return "Simulación Pushover enviada."
    user = os.environ.get("PUSHOVER_USER")
    token = os.environ.get("PUSHOVER_TOKEN")
    
    try:
        requests.post("https://api.pushover.net/1/messages.json",
                      data={"token": token, "user": user, "message": msg}, timeout=10)
        return "Pushover enviado."
    except Exception as e: return f"Error Pushover: {e}"

@tool("Enviar WhatsApp")
def send_whatsapp(message: str) -> str:
    """Envía WhatsApp vía Twilio."""
    if DRY_RUN: return "Simulación WhatsApp enviada."
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_num = os.environ.get("TWILIO_FROM_NUMBER")
    to_num = os.environ.get("WHATSAPP_PHONE")
    
    if not all([sid, token, from_num, to_num]): return "Faltan credenciales Twilio."
    
    try:
        client = Client(sid, token)
        msg = client.messages.create(body=message[:1500], from_=from_num, to=to_num)
        return f"WhatsApp enviado ID: {msg.sid}"
    except Exception as e: return f"Error WhatsApp: {e}"