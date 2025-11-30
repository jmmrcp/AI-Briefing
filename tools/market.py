import json
import requests
import feedparser
import yfinance as yf
from crewai.tools import tool
from config import CLAVES_FINANCIERAS

@tool("Noticias RSS")
def get_financial_news(busqueda: str) -> str:
    """Busca noticias en Google News."""
    base_url = "https://news.google.com/rss/search"
    params = {"q": busqueda, "hl": "es-ES", "gl": "ES", "ceid": "ES:es"}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resp = requests.get(base_url, params=params, headers=headers, timeout=10)
        f = feedparser.parse(resp.content)
        noticias = [{"titulo": e.title, "link": e.link} for e in f.entries[:5]]
        return json.dumps({"news": noticias}, ensure_ascii=False)
    except Exception as e: return json.dumps({"error": str(e)})

@tool("Bolsa")
def get_stock_price(symbol: str) -> str:
    """Obtiene datos de Yahoo Finance."""
    try:
        t = yf.Ticker(symbol.strip().upper())
        info = t.info
        datos = {k: info.get(k) for k in CLAVES_FINANCIERAS if info.get(k) is not None}
        return json.dumps({"stock": datos}, indent=2, ensure_ascii=False)
    except Exception as e: return json.dumps({"error": str(e)})