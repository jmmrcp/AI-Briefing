# 🤖 AI Executive Assistant: Modular & Autonomous

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![CrewAI](https://img.shields.io/badge/AI-CrewAI-orange)
![Structure](https://img.shields.io/badge/Architecture-Modular-purple)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

Un sistema de **Agentes de IA Autónomos** diseñado para actuar como un Jefe de Gabinete personal. Este "Crew" se despierta, consulta múltiples fuentes de datos (Gmail, Calendar, Bolsa, Transporte Urbano) y redacta un **Briefing Matutino** conciso y accionable, enviándolo directamente a tu móvil.

---

## 📂 Nueva Estructura del Proyecto

El proyecto ha sido refactorizado para ser modular, escalable y fácil de mantener:

```text
ai-assistant/
├── main.py                  # 🚀 Punto de entrada principal
├── config.py                # ⚙️ Configuración global y Logs
├── auth.py                  # 🔐 Autenticación Google y LLM
├── crew_setup.py            # 🕵️ Definición del Equipo (Agentes y Tareas)
├── tools/                   # 🧰 Paquete de Herramientas
│   ├── __init__.py
│   ├── google_suite.py      # Gmail, Calendar, Tasks
│   ├── market.py            # Yahoo Finance, RSS Noticias
│   ├── messaging.py         # Telegram, WhatsApp, Pushover
│   └── transport.py         # OCR y Transporte Urbano
├── Dockerfile               # 🐳 Configuración de contenedor
├── requirements.txt         # Dependencias Python
└── .github/workflows/       # 🤖 Automatización GitHub Actions
```

---

## 🛠️ Requisitos Previos

1.  **Google Cloud Project:** Archivo `credentials.json` con permisos para Gmail, Calendar y Tasks API.
2.  **Tesseract OCR:** Motor de reconocimiento óptico (necesario para leer boletines de transporte).
3.  **Claves API:** Google Gemini, Telegram/Twilio/Pushover.

---

## 🐳 Ejecución con Docker (Recomendado)

Docker es la forma más sencilla de ejecutar el asistente, ya que gestiona automáticamente la instalación de **Tesseract OCR** y el idioma español.

### 1. Preparación
Asegúrate de tener en la carpeta raíz:
*   `.env` (con tus variables)
*   `credentials.json` (de Google)
*   `token.json` (si ya te has autenticado previamente, si no, ejecuta en local primero).

### 2. Construir la imagen
```bash
docker build -t ai-assistant .
```

### 3. Ejecutar el contenedor
Es crucial usar **volúmenes (-v)** para que el contenedor pueda leer tus credenciales y mantener la sesión de Google iniciada.

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  ai-assistant
```

---

## 🤖 Automatización con GitHub Actions

Este repositorio incluye un flujo de trabajo (`.github/workflows/morning_briefing.yml`) configurado para ejecutarse automáticamente (ej. a las 06:00 AM).

### Configuración de Secretos (IMPORTANTE)
Dado que `credentials.json` y `token.json` son archivos físicos y no deben subirse al repositorio público, los inyectamos codificados en **Base64**.

1.  Ve a tu repo en GitHub > **Settings** > **Secrets and variables** > **Actions**.
2.  Crea los siguientes secretos:

| Nombre del Secreto | Valor a introducir |
| :--- | :--- |
| `ENV_FILE` | Copia y pega todo el contenido de tu archivo `.env`. |
| `CREDENTIALS_JSON_B64` | El contenido de `credentials.json` convertido a Base64 string. |
| `TOKEN_JSON_B64` | El contenido de `token.json` convertido a Base64 string. |
| `GOOGLE_API_KEY` | Tu clave de Gemini (opcional si ya está en ENV_FILE). |
| `TELEGRAM_TOKEN` | Tu token de Telegram (opcional si ya está en ENV_FILE). |

#### 💡 Cómo obtener la cadena Base64
Ejecuta esto en tu terminal local y copia el resultado:

*   **Mac/Linux:**
    ```bash
    base64 -i credentials.json | pbcopy
    # Haz lo mismo para token.json
    ```
*   **Windows (PowerShell):**
    ```powershell
    [Convert]::ToBase64String([IO.File]::ReadAllBytes("credentials.json"))
    ```

---

## 🚀 Instalación Local (Desarrollo)

Si prefieres ejecutarlo en tu máquina sin Docker:

1.  **Instalar Tesseract OCR (Sistema):**
    *   Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-spa libtesseract-dev`
    *   Mac: `brew install tesseract-lang`
2.  **Entorno Virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # O venv\Scripts\activate en Windows
    pip install -r requirements.txt
    ```
3.  **Ejecutar:**
    ```bash
    python main.py
    ```

---

## 📄 Licencia
Este proyecto está bajo la licencia MIT.
```