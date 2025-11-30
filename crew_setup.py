# crew_setup.py
from datetime import datetime
from crewai import Crew, Agent, Task
from auth import get_llm

# Importar herramientas desde el paquete
from tools.google_suite import read_emails, get_todays_agenda, get_todays_tasks
from tools.market import get_stock_price, get_financial_news
from tools.transport import inc_transport
from tools.messaging import send_telegram, send_pushover

def create_crew():
    llm = get_llm()
    fecha = datetime.now().strftime('%d/%m/%Y')

    # Agentes
    transport_agent = Agent(
        role="Analista Transporte",
        goal="Detectar incidencias en transporte hoy.",
        backstory="Experto en logística urbana. Usas OCR para leer boletines.",
        llm=llm, tools=[inc_transport], verbose=False
    )
    
    mail_agent = Agent(
        role="Analista Correo",
        goal="Filtrar correo urgente.",
        backstory="EA senior. Solo reportas lo vital.",
        llm=llm, tools=[read_emails], verbose=False
    )

    calendar_agent = Agent(
        role="Auditor Agenda",
        goal="Listar eventos exactos.",
        backstory="Bot estricto. No inventas reuniones.",
        llm=llm, tools=[get_todays_agenda], verbose=False
    )

    task_agent = Agent(
        role="Gestor Tareas",
        goal="Listar tareas vencidas.",
        backstory="Revisas Google Tasks.",
        llm=llm, tools=[get_todays_tasks], verbose=False
    )

    analyst_agent = Agent(
        role="Analista Mercado",
        goal="Info bursátil clave.",
        backstory="Analista de datos financieros.",
        llm=llm, tools=[get_stock_price, get_financial_news], verbose=False
    )

    briefing_agent = Agent(
        role="Jefe de Gabinete",
        goal="Generar y enviar reporte.",
        backstory="Consolidas info y envías el resumen final.",
        llm=llm, tools=[send_telegram, send_pushover], verbose=True
    )

    # Tareas
    t_trans = Task(description="Busca incidencias transporte hoy.", expected_output="Alertas transporte.", agent=transport_agent)
    t_mail = Task(description=f"Correos importantes de hoy {fecha}.", expected_output="Resumen correos.", agent=mail_agent)
    t_cal = Task(description=f"Agenda real de hoy {fecha}.", expected_output="Lista eventos.", agent=calendar_agent)
    t_task = Task(description=f"Tareas para hoy {fecha}.", expected_output="Lista tareas.", agent=task_agent)
    t_fin = Task(description="Precio REP.MC y noticias relevantes.", expected_output="Datos financieros.", agent=analyst_agent)

    t_briefing = Task(
        description=f"""Genera BRIEFING {fecha}.
        Estructura: 
        1. 📅 Agenda
        2. ✅ Tareas
        3. 📧 Correos
        4. 📈 Mercado
        5. 🚚 Transporte
        NO inventes datos. Envía por Telegram.""",
        expected_output="Reporte enviado.",
        agent=briefing_agent,
        context=[t_trans, t_mail, t_cal, t_task, t_fin]
    )

    return Crew(
        agents=[transport_agent, mail_agent, calendar_agent, task_agent, analyst_agent, briefing_agent],
        tasks=[t_trans, t_mail, t_cal, t_task, t_fin, t_briefing],
        verbose=True
    )