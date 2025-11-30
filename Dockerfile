# Usamos una imagen base ligera de Python
FROM python:3.12-slim

# Evita que Python genere archivos .pyc y habilita logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. Instalar dependencias del sistema y Tesseract con español
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Configurar directorio de trabajo
WORKDIR /app

# 3. Copiar requirements e instalar librerías Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el resto del código
COPY . .

# 5. Comando por defecto
CMD ["python", "main.py"]
