
import os
import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
GEMINI_KEY = os.environ.get("API_KEY")
BREVO_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")

# Safe Initialization
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase Init Error: {e}")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

class Task(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    date: str
    priority: str
    completed: bool = False

def send_email(to_email: str, subject: str, content: str):
    if not BREVO_KEY or not SENDER_EMAIL:
        return "Email configuration missing."
    
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email}],
        sender={"email": SENDER_EMAIL, "name": "MorningZen"},
        subject=subject,
        html_content=f"<html><body style='font-family: sans-serif; line-height: 1.6; color: #334155;'><div style='max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;'>{content}</div></body></html>"
    )
    try:
        api_instance.send_trans_email(send_smtp_email)
        return "Sent"
    except ApiException as e:
        return f"Brevo Error: {e}"

def get_ai_briefing(tasks):
    if not GEMINI_KEY:
        return "AI Briefing unavailable (API key missing)."
    
    model = genai.GenerativeModel('gemini-3-flash-preview')
    task_str = "\n".join([f"- {t['title']} ({t['priority']})" for t in tasks]) if tasks else "No tasks for today! Enjoy the peace."
    
    prompt = f"""
    Act as a Zen productivity coach. It is 8:00 AM. 
    1. Provide a calming, short quote.
    2. Write a 2-sentence warm greeting.
    3. Review these tasks and give a one-sentence high-level strategy for today:
    {task_str}
    
    Keep it elegant, short, and motivating. Use Markdown-style line breaks.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Briefing Error: {str(e)}"

# Routes
@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "supabase": supabase is not None,
        "gemini": GEMINI_KEY is not None,
        "brevo": BREVO_KEY is not None,
        "sender": SENDER_EMAIL
    }

@app.get("/api/tasks")
async def list_tasks():
    if not supabase: return []
    res = supabase.table("tasks").select("*").order("date").execute()
    return res.data

@app.post("/api/tasks")
async def add_task(task: Task):
    if not supabase: raise HTTPException(status_code=500, detail="DB Offline")
    data = task.dict(exclude_none=True)
    res = supabase.table("tasks").insert(data).execute()
    return res.data[0]

@app.patch("/api/tasks/{task_id}/toggle")
async def toggle(task_id: str):
    if not supabase: raise HTTPException(status_code=500, detail="DB Offline")
    res = supabase.table("tasks").select("completed").eq("id", task_id).execute()
    new_val = not res.data[0]['completed']
    supabase.table("tasks").update({"completed": new_val}).eq("id", task_id).execute()
    return {"status": "ok"}

@app.delete("/api/tasks/{task_id}")
async def remove_task(task_id: str):
    if not supabase: raise HTTPException(status_code=500, detail="DB Offline")
    supabase.table("tasks").delete().eq("id", task_id).execute()
    return {"status": "deleted"}

@app.get("/api/cron")
async def daily_cron_trigger():
    if not supabase: return {"error": "DB Offline"}
    today = datetime.date.today().isoformat()
    res = supabase.table("tasks").select("*").eq("date", today).eq("completed", False).execute()
    briefing = get_ai_briefing(res.data)
    email_status = send_email(SENDER_EMAIL, "Your MorningZen Briefing", briefing.replace("\n", "<br>"))
    return {"status": "processed", "email": email_status, "tasks_found": len(res.data)}
