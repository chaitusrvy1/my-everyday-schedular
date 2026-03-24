
import os
import datetime
import httpx
import random
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from google import genai
from google.genai import types

# Standard FastAPI initialization for Vercel
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
BREVO_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Safe Initialization
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase Init Error: {e}")

class TaskItem(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    date: str
    priority: str
    completed: bool = False

class UserSettings(BaseModel):
    email: str
    name: Optional[str] = "Zen User"

async def generate_gemini_briefing(tasks: List[dict], user_name: str):
    """Generates a personalized briefing using Gemini AI."""
    if not GEMINI_API_KEY:
        return "Gemini API key missing. Please configure it in environment variables."
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    task_str = "\n".join([f"- {t['title']} (Priority: {t['priority']})" for t in tasks])
    prompt = f"""
    You are a calm, motivational morning coach. 
    User Name: {user_name}
    Today's Tasks:
    {task_str if tasks else "No tasks scheduled. A day of rest and reflection."}

    Write a short, beautiful morning briefing (max 150 words). 
    Include:
    1. A warm greeting.
    2. A unique, relevant motivational quote.
    3. A brief, encouraging summary of their day's intentions.
    4. A final 'Zen' thought for the day.
    
    Format the output with HTML tags like <h2>, <p>, and <i> for a beautiful email.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return f"<p>Good morning {user_name}! You have {len(tasks)} tasks today. Stay focused!</p>"

async def send_email_via_api(to_email: str, subject: str, content: str):
    """Sends email using Brevo REST API directly."""
    if not BREVO_KEY or not SENDER_EMAIL:
        return "Email configuration missing (BREVO_KEY or SENDER_EMAIL)."
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "MorningZen", "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body style='font-family: sans-serif; line-height: 1.6; color: #334155;'><div style='max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;'>{content}</div></body></html>"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            if response.status_code >= 400:
                return f"Brevo API Error: {response.status_code} - {response.text}"
            return "Sent"
        except Exception as e:
            return f"HTTP Error: {str(e)}"

def get_simple_briefing(tasks):
    """Provides a lightweight Zen briefing."""
    quotes = [
        "The sun rises every day, offering a new chance to begin.",
        "Peace comes from within. Do not seek it without.",
        "Do not dwell in the past, do not dream of the future, concentrate the mind on the present moment.",
        "Be where you are; otherwise you will miss your life."
    ]
    quote = random.choice(quotes)
    
    task_list = "<br>".join([f"• {t['title']} ({t['priority']})" for t in tasks]) if tasks else "No tasks scheduled for today. Enjoy the stillness."
    
    return f"""
    <h2 style='color: #f97316; font-style: italic;'>MorningZen</h2>
    <p style='font-size: 1.1em; color: #64748b;'><i>\"{quote}\"</i></p>
    <hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;'>
    <p>Good Morning! Here is your plan for the day.</p>
    <div style='background: #f8fafc; padding: 15px; border-radius: 8px;'>
        <strong>Today's Intentions:</strong><br>
        {task_list}
    </div>
    <p style='margin-top: 20px; font-size: 0.9em; color: #94a3b8;'>Stay focused and present.</p>
    """

# --- ROUTES (EXPLICIT /API PREFIX FOR VERCEL) ---

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "supabase": supabase is not None,
        "brevo": BREVO_KEY is not None,
        "sender": SENDER_EMAIL,
        "api_ready": True
    }

@app.get("/api/tasks")
async def list_tasks():
    if not supabase: return []
    try:
        res = supabase.table("tasks").select("*").order("date").execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Supabase Select Error: {e}")
        return []

@app.post("/api/tasks")
async def add_task(task: TaskItem):
    if not supabase: raise HTTPException(status_code=503, detail="Database connection not initialized")
    try:
        data = task.dict(exclude_none=True)
        if 'id' in data: del data['id']
        res = supabase.table("tasks").insert(data).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/tasks/{task_id}/toggle")
async def toggle(task_id: str):
    if not supabase: raise HTTPException(status_code=503, detail="Database offline")
    try:
        res = supabase.table("tasks").select("completed").eq("id", task_id).execute()
        if not res.data: raise HTTPException(status_code=404, detail="Task not found")
        new_val = not res.data[0]['completed']
        supabase.table("tasks").update({"completed": new_val}).eq("id", task_id).execute()
        return {"status": "ok", "completed": new_val}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def remove_task(task_id: str):
    if not supabase: raise HTTPException(status_code=503, detail="Database offline")
    try:
        supabase.table("tasks").delete().eq("id", task_id).execute()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
async def save_settings(settings: UserSettings):
    if not supabase: raise HTTPException(status_code=503, detail="Database offline")
    try:
        # We use a fixed ID for single user settings for now
        res = supabase.table("settings").upsert({
            "id": "main_user",
            "email": settings.email,
            "name": settings.name
        }).execute()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
async def get_settings():
    if not supabase: return {"email": "", "name": "Zen User"}
    try:
        res = supabase.table("settings").select("*").eq("id", "main_user").execute()
        if res.data:
            return res.data[0]
        return {"email": "", "name": "Zen User"}
    except Exception as e:
        return {"email": "", "name": "Zen User"}

@app.get("/api/cron")
async def daily_cron_trigger():
    if not supabase: return {"error": "Database offline"}
    try:
        # 1. Get User Settings
        settings_res = supabase.table("settings").select("*").eq("id", "main_user").execute()
        if not settings_res.data:
            return {"error": "No user settings found. Please configure your email in the app."}
        
        user_email = settings_res.data[0]['email']
        user_name = settings_res.data[0].get('name', 'Zen User')

        # 2. Get Today's Tasks
        today = datetime.date.today().isoformat()
        res = supabase.table("tasks").select("*").eq("date", today).eq("completed", False).execute()
        
        # 3. Generate AI Briefing
        briefing_html = await generate_gemini_briefing(res.data, user_name)
        
        # 4. Send Email
        email_status = await send_email_via_api(user_email, "Your MorningZen Briefing", briefing_html)
        
        return {"status": "processed", "email": email_status, "tasks_found": len(res.data)}
    except Exception as e:
        return {"error": str(e)}
