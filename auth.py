# auth.py
import os
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from crewai import LLM

from config import SCOPES, logger

def get_llm():
    """Retorna instancia LLM configurada."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Falta GOOGLE_API_KEY en .env")

    return LLM(
        model="gemini/gemini-flash-latest",
        verbose=True,
        temperature=0,
        google_api_key=api_key
    )

def authenticate_google() -> Optional[Credentials]:
    """Maneja el flujo OAuth 2.0."""
    creds = None
    token_file = 'token.json'
    creds_file = 'credentials.json'

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("🔄 Token refrescado.")
            except Exception:
                logger.warning("⚠️ Token expirado. Re-autenticando...")
                creds = None

        if not creds:
            if not os.path.exists(creds_file):
                logger.error("❌ Falta credentials.json")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return creds