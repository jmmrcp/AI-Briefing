import json
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from crewai.tools import tool
from auth import authenticate_google

@tool("Leer correo")
def read_emails() -> str:
    """Lee correos prioritarios de hoy."""
    creds = authenticate_google()
    if not creds: return "Error auth."
    
    service = build("gmail", "v1", credentials=creds)
    hoy = datetime.now().strftime("%Y/%m/%d")
    mañana = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")
    
    results = service.users().messages().list(userId='me', q=f"after:{hoy} before:{mañana} category:primary", maxResults=20).execute()
    msgs = results.get('messages', [])
    
    correos = []
    for m in msgs:
        txt = service.users().messages().get(userId='me', id=m['id']).execute()
        headers = txt.get('payload', {}).get('headers', [])
        subj = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin Asunto')
        correos.append({"asunto": subj, "snippet": txt.get('snippet', '')[:100]})
        
    return json.dumps(correos, ensure_ascii=False)

@tool("Calendario")
def get_todays_agenda() -> str:
    """Agenda de hoy."""
    creds = authenticate_google()
    if not creds: return "Error auth."
    service = build("calendar", "v3", credentials=creds)
    
    now = datetime.now()
    t_min = now.replace(hour=0, minute=0).isoformat() + 'Z'
    t_max = now.replace(hour=23, minute=59).isoformat() + 'Z'
    
    events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute()
    agenda = [{"titulo": e.get('summary'), "inicio": e['start'].get('dateTime')} for e in events.get('items', [])]
    return json.dumps(agenda, ensure_ascii=False)

@tool("Tareas")
def get_todays_tasks() -> str:
    """Tareas para hoy."""
    creds = authenticate_google()
    if not creds: return "Error auth."
    service = build("tasks", "v1", credentials=creds)
    
    tareas = []
    tasklists = service.tasklists().list(maxResults=5).execute()
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    
    for lista in tasklists.get('items', []):
        tasks = service.tasks().list(tasklist=lista['id'], showCompleted=False).execute()
        for t in tasks.get('items', []):
            if t.get('due', '').startswith(hoy_str):
                tareas.append({"titulo": t['title'], "lista": lista['title']})
                
    return json.dumps(tareas, ensure_ascii=False)