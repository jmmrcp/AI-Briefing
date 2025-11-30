import requests
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from urllib.parse import urlparse
from crewai.tools import tool

@tool("Transporte")
def inc_transport():
    """OCR para incidencias de transporte."""
    URL = 'https://tmpmurcia.es/ultima.asp'
    try:
        resp = requests.get(URL, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Buscar enlace del día
        enlace = None
        parsed = urlparse(URL)
        base = f"{parsed.scheme}://{parsed.netloc}/"
        for a in soup.find_all('a', href=True):
            if "Cuerpo.asp?codigo=" in a['href']:
                enlace = base + a['href']
                break
        
        if not enlace: return "No hay parte diario."
        
        # Buscar imagen
        r = requests.get(enlace, timeout=15)
        sub_soup = BeautifulSoup(r.text, 'html.parser')
        img_tag = sub_soup.find('img', src=lambda x: x and '/fotos/noticias/' in x)
        
        if not img_tag: return "No imagen encontrada."
        
        img_url = img_tag['src']
        if not img_url.startswith('http'): img_url = f"https://tmpmurcia.es/{img_url.lstrip('/')}"
        
        # OCR
        img_data = requests.get(img_url, timeout=15).content
        imagen = Image.open(BytesIO(img_data))
        
        # Intento robusto de OCR (Español -> Inglés fallback)
        try:
            texto = pytesseract.image_to_string(imagen, lang='spa')
        except:
            texto = pytesseract.image_to_string(imagen, lang='eng')
            
        return {"texto": texto[:600], "enlace": enlace}
        
    except Exception as e: return f"Error transporte: {e}"