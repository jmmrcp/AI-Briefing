#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import json
import urllib.parse
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

# Librerías externas
import requests
import feedparser
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv

# Google APIs
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# CrewAI
from crewai import Crew, Agent, Task, LLM
from crewai.tools import tool

# Twilio
from twilio.rest import Client

# Procesamiento de HTML y OCR
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from urllib.parse import urlparse

# ==========================
# Configuración Inicial
# ==========================

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Logging
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    level=getattr(logging, log_level),
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constantes y Scopes
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
    "https://www.googleapis.com/auth/gmail.readonly"
]
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# Campos financieros a extraer
CLAVES_PRINCIPALES = [
    "symbol", "shortName", "currency", "exchange",
    "currentPrice", "regularMarketPrice", "previousClose",
    "regularMarketChangePercent", "dayLow", "dayHigh",
    "fiftyTwoWeekLow", "fiftyTwoWeekHigh", "marketCap", "dividendYield"
]

# ==========================
# Autenticación y LLM
# ==========================

def get_llm():
    """Retorna una instancia configurada del LLM."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.critical("GOOGLE_API_KEY no encontrada en variables de entorno.")
        raise ValueError("Falta GOOGLE_API_KEY")

    return LLM(
        model="gemini/gemini-flash-latest",
        verbose=True,
        temperature=0,
        google_api_key=api_key
    )

def authenticate_google_services() -> Optional[Credentials]:
    """Maneja el flujo de autenticación OAuth 2.0."""
    creds = None
    token_file = 'token.json'
    creds_file = 'credentials.json'

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("🔄 Token refrescado automáticamente")
            except Exception:
                logger.warning("⚠️ Token expirado. Re-autenticando...")
                creds = None

        if not creds:
            if not os.path.exists(creds_file):
                logger.error(f"❌ Faltan '{creds_file}'. Descárgalo de Google Cloud Console.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return creds

# ==========================
# Herramientas (Tools)
# ==========================

@tool("Enviar Telegram")
def send_telegram(message: str) -> str:
    """Envía el reporte a Telegram."""
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return "Error: Faltan credenciales de Telegram."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=payload, timeout=10)
        return "Telegram enviado." if response.status_code == 200 else f"Error Telegram: {response.text}"
    except Exception as e:
        return f"Excepción Telegram: {e}"

@tool("Noticias RSS")
def get_financial_news(busqueda: str) -> str:
    """Busca noticias recientes en Google News (RSS)."""
    base_url = "https://news.google.com/rss/search"
    params = {"q": busqueda, "hl": "es-ES", "gl": "ES", "ceid": "ES:es"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        f = feedparser.parse(response.content)
        noticias_procesadas = []

        if not f.entries:
            return json.dumps({"news": [], "mensaje": f"Sin noticias para '{busqueda}'."}, ensure_ascii=False)

        for entry in f.entries[:5]:
            noticias_procesadas.append({
                "titulo": entry.title,
                "link": entry.link,
                "fecha": entry.get("published", "Fecha desconocida"),
                "fuente": entry.get("source", {}).get("title", "Google News")
            })
        return json.dumps({"news": noticias_procesadas}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e), "news": []}, ensure_ascii=False)

@tool("Bolsa")
def get_stock_price(symbol: str) -> str:
    """Obtiene datos financieros filtrados de Yahoo Finance."""
    try:
        t = yf.Ticker(symbol.strip().upper())
        info = t.info
        if not info or ('currentPrice' not in info and 'regularMarketPrice' not in info):
             return json.dumps({"error": "Ticker inválido", "stock": {}}, ensure_ascii=False)
        
        datos = {k: info.get(k) for k in CLAVES_PRINCIPALES if info.get(k) is not None}
        return json.dumps({"stock": datos}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool("Enviar Pushover")
def send_pushover(msg: str) -> str:
    """Envía notificaciones vía Pushover."""
    if DRY_RUN: return "Simulación: Enviado."
    user = os.environ.get("PUSHOVER_USER")
    token = os.environ.get("PUSHOVER_TOKEN")
    
    if not user or not token: return "Error: Faltan credenciales Pushover."

    try:
        resp = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": token, "user": user, "message": msg, "title": "Briefing IA"},
            timeout=10
        )
        return "Enviado." if resp.status_code == 200 else f"Error API: {resp.text}"
    except Exception as e:
        return f"Excepción Pushover: {e}"

@tool("Enviar WhatsApp")
def send_whatsapp(message: str) -> str:
    """Envía un mensaje de WhatsApp utilizando la API de Twilio."""
    if DRY_RUN: return "Simulación: Enviado (DRY_RUN)"
    
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_num = os.environ.get("TWILIO_FROM_NUMBER")
    to_num = os.environ.get("WHATSAPP_PHONE")

    if not all([sid, token, from_num, to_num]):
        return json.dumps({"error": "Configuración incompleta de Twilio"})

    try:
        client = Client(sid, token)
        msg = client.messages.create(
            body=message[:1500],
            from_=f"whatsapp:{from_num}" if not from_num.startswith("whatsapp:") else from_num,
            to=f"whatsapp:{to_num}" if not to_num.startswith("whatsapp:") else to_num
        )
        return json.dumps({"resultado": "Enviado", "id": msg.sid})
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool("Leer correo")
def read_emails() -> str:
    """Lee correos de hoy filtrando 'category:primary'."""
    try:
        creds = authenticate_google_services()
        if not creds: return json.dumps({"error": "Fallo autenticación"})
        
        service = build("gmail", "v1", credentials=creds)
        hoy = datetime.now().strftime("%Y/%m/%d")
        mañana = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")
        
        # Filtro estricto para reducir ruido
        query = f"after:{hoy} before:{mañana} category:primary"
        
        results = service.users().messages().list(userId='me', q=query, maxResults=20).execute()
        messages = results.get('messages', [])
        
        correos = []
        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = txt.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(Sin Asunto)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Desconocido)')
            correos.append({"remitente": sender, "asunto": subject, "resumen": txt.get('snippet', '')[:150]})
            
        if not correos: return json.dumps({"correos": [], "mensaje": "Bandeja limpia."})
        return json.dumps({"correos": correos}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool("Calendario")
def get_todays_agenda() -> str:
    """Obtiene eventos de hoy del calendario principal."""
    try:
        creds = authenticate_google_services()
        if not creds: return json.dumps({"error": "Fallo autenticación"})

        service = build("calendar", "v3", credentials=creds)
        now = datetime.now()
        time_min = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary', timeMin=time_min, timeMax=time_max,
            singleEvents=True, orderBy='startTime'
        ).execute()

        agenda = []
        for event in events_result.get('items', []):
            start = event['start'].get('dateTime', event['start'].get('date'))
            agenda.append({
                "titulo": event.get('summary', 'Sin título'),
                "inicio": start,
                "ubicacion": event.get('location', 'N/A')
            })

        if not agenda: return json.dumps({"agenda": [], "mensaje": "Agenda libre."}, ensure_ascii=False)
        return json.dumps({"agenda": agenda}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool("Tareas")
def get_todays_tasks() -> str:
    """Obtiene tareas que vencen hoy."""
    try:
        creds = authenticate_google_services()
        if not creds: return json.dumps({"error": "Fallo autenticación"})
        
        service = build("tasks", "v1", credentials=creds)
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        tareas = []
        
        tasklists = service.tasklists().list(maxResults=5).execute()
        for lista in tasklists.get('items', []):
            tasks = service.tasks().list(tasklist=lista['id'], showCompleted=False).execute()
            for t in tasks.get('items', []):
                due = t.get('due')
                if due and due.startswith(hoy_str):
                    tareas.append({
                        "lista": lista['title'],
                        "titulo": t['title'],
                        "notas": t.get('notes', '')
                    })
        
        if not tareas: return json.dumps({"tareas": [], "mensaje": "Sin tareas."}, ensure_ascii=False)
        return json.dumps({"tareas": tareas}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool("Transporte")
def inc_transport():
    """Obtiene problemas en el transporte mediante OCR."""
    URL = 'https://tmpmurcia.es/ultima.asp'
    try:
        parsed = urlparse(URL)
        dominio = f"{parsed.scheme}://{parsed.netloc}/"
        
        resp = requests.get(URL, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        enlace = None
        for a in soup.find_all('a', href=True):
            if "Cuerpo.asp?codigo=" in a['href']:
                enlace = dominio + a['href']
                break
        
        if not enlace: return {"error": "No se encontró enlace del día"}

        r = requests.get(enlace, timeout=15)
        sub_soup = BeautifulSoup(r.text, 'html.parser')
        
        img_tag = sub_soup.find('img', src=lambda x: x and '/fotos/noticias/' in x)
        if not img_tag: return {'error': 'No se encontró imagen'}
        
        img_url = img_tag['src']
        if not img_url.startswith('http'):
            img_url = f"https://tmpmurcia.es/{img_url.lstrip('/')}"
            
        img_resp = requests.get(img_url, timeout=15)
        imagen = Image.open(BytesIO(img_resp.content))
        
        try:
            texto = pytesseract.image_to_string(imagen, lang='spa')
        except pytesseract.TesseractError as e:
            logger.warning(f"⚠️ Falló OCR en español, intentando inglés. Error: {e}")
            try:
                # Intento fallback (inglés o default)
                texto = pytesseract.image_to_string(imagen, lang='eng')
            except Exception as e2:
                return {'error': f"Fallo crítico OCR: {str(e2)}"}
            
        lineas = texto.splitlines()
        ocurrencias_44 = [line for line in lineas if '44' in line]
        
        return {
            'pagina': enlace,
            'ocurrencias_44': ocurrencias_44,
            'texto_resumen': texto[:500]
        }
    except Exception as e:
        return {'error': f"Fallo Transporte: {str(e)}"}

# ==========================
# Definición de Agentes
# ==========================

def create_crew():
    llm = get_llm()

    transport_agent = Agent(
        role="Analista de incidencias de transporte",
        goal="Identificar problemas de transporte hoy.",
        backstory="Especialista en logística urbana. 'Ves' los boletines oficiales usando OCR.",
        llm=llm,
        tools=[inc_transport],
        verbose=False
    )

    mail_agent = Agent(
        role="Analista de Comunicaciones",
        goal="Revisar correo importante.",
        backstory="EA de alto nivel. Filtras spam y destacas lo urgente.",
        llm=llm,
        tools=[read_emails],
        verbose=False
    )

    calendar_agent = Agent(
        role="Auditor de Calendario",
        goal="Listar eventos REALES. No inventar nada.",
        backstory="Eres un bot estricto. Si no hay eventos, reportas 'Vacío'.",
        llm=llm,
        tools=[get_todays_agenda],
        verbose=False
    )

    task_agent = Agent(
        role="Gestor de Tareas",
        goal="Listar tareas vencidas hoy.",
        backstory="Solo importan las tareas registradas en Google Tasks.",
        llm=llm,
        tools=[get_todays_tasks],
        verbose=False
    )

    analyst_agent = Agent(
        role="Analista de Mercado",
        goal="Datos de 'El Corte Inglés' y 'Repsol'.",
        backstory="Analista bursátil basado en datos duros.",
        llm=llm,
        tools=[get_stock_price, get_financial_news],
        verbose=False
    )

    briefing_agent = Agent(
        role="Jefe de Gabinete",
        goal="Consolidar info veraz y enviar reporte.",
        backstory="Generas el Briefing diario. NO inventas datos. Envías por Telegram/Whatsapp.",
        llm=llm,
        tools=[send_pushover, send_telegram], # Añade send_whatsapp si tienes Twilio configurado
        verbose=False
    )

    # Tareas
    fecha_hoy = datetime.now().strftime('%d/%m/%Y')

    t_mail = Task(description=f"Lee correos de hoy ({fecha_hoy}). Resume.", expected_output="Lista JSON correos.", agent=mail_agent)
    t_cal = Task(description=f"Agenda de hoy ({fecha_hoy}). Solo datos reales.", expected_output="Lista eventos.", agent=calendar_agent)
    t_task = Task(description=f"Tareas para hoy ({fecha_hoy}).", expected_output="Lista tareas.", agent=task_agent)
    t_fin = Task(description="Precio REP.MC y noticias ECI.", expected_output="Datos fin y noticias.", agent=analyst_agent)
    t_trans = Task(description="Incidencias transporte hoy.", expected_output="Alertas transporte.", agent=transport_agent)
    
    t_briefing = Task(
        description=f"""Genera BRIEFING {fecha_hoy}. Estructura:
        1. 📅 Agenda (si hay)
        2. ✅ Tareas (si hay)
        3. 📧 Correos (si hay)
        4. 📈 Mercado
        5. 🚚 Transporte
        NO inventes datos. Envía el reporte a Telegram/Pushover.""",
        expected_output="Reporte enviado.",
        agent=briefing_agent,
        context=[t_mail, t_cal, t_task, t_fin, t_trans]
    )

    return Crew(
        agents=[mail_agent, calendar_agent, task_agent, analyst_agent, transport_agent, briefing_agent],
        tasks=[t_mail, t_cal, t_task, t_fin, t_trans, t_briefing],
        verbose=True
    )

# ==========================
# Ejecución Principal
# ==========================

if __name__ == "__main__":
    print("🚀 Iniciando AI Executive Assistant...")
    try:
        crew = create_crew()
        result = crew.kickoff()
        print("\n✅ Ejecución finalizada.")
        print("Resultado final:\n")
        print(result)
    except Exception as e:
        logger.critical(f"🔥 Error crítico: {e}")