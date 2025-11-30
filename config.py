# config.py
import os
import sys
import logging
from dotenv import load_dotenv

# Cargar variables
load_dotenv()

# Configuración de Logging
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    level=getattr(logging, log_level),
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AI_Assistant")

# Constantes
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
    "https://www.googleapis.com/auth/gmail.readonly"
]

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# Datos financieros a extraer
CLAVES_FINANCIERAS = [
    "symbol", "shortName", "currency", "exchange",
    "currentPrice", "regularMarketPrice", "previousClose",
    "regularMarketChangePercent", "dayLow", "dayHigh",
    "fiftyTwoWeekLow", "fiftyTwoWeekHigh", "marketCap"
]