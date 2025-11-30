# main.py
import sys
from crew_setup import create_crew
from config import logger

if __name__ == "__main__":
    logger.info("🚀 Iniciando Sistema Modular de Agentes...")
    try:
        crew = create_crew()
        result = crew.kickoff()
        logger.info("✅ Ejecución completada.")
        print("\n--- RESULTADO FINAL ---\n")
        print(result)
    except Exception as e:
        logger.critical(f"🔥 Fallo crítico: {e}")
        sys.exit(1)