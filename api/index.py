
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
from dotenv import load_dotenv

# Load environment variables from .env file
# Try root first, then api/
load_dotenv()
load_dotenv(os.path.join(os.getcwd(), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Standard FastAPI initialization for Vercel
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
# Try multiple names for each key to be robust
def get_env_robust(keys: List[str]):
    for key in keys:
        val = os.environ.get(key)
        if val and not is_placeholder(val):
            return val
    return None

SUPABASE_URL = get_env_robust(["SUPABASE_URL", "VITE_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"])
SUPABASE_KEY = get_env_robust([
    "SUPABASE_ANON_KEY", "VITE_SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_KEY", "SUPABASE_SERVICE_ROLE_KEY"
])
BREVO_KEY = get_env_robust(["BREVO_API_KEY", "VITE_BREVO_API_KEY", "SENDINBLUE_API_KEY"])
SENDER_EMAIL = get_env_robust(["SENDER_EMAIL", "VITE_SENDER_EMAIL", "BREVO_SENDER_EMAIL"])
GEMINI_API_KEY = get_env_robust(["GEMINI_API_KEY", "VITE_GEMINI_API_KEY", "GOOGLE_API_KEY", "API_KEY"])

def is_placeholder(val):
    if not val: return True
    placeholders = [
        "your_supabase_project_url", 
        "your_supabase_anon_key", 
        "your_google_ai_studio_api_key", 
        "your_brevo_api_key", 
        "your_verified_brevo_sender_email"
    ]
    return val in placeholders

def mask_key(key):
    if not key: return "MISSING"
    if is_placeholder(key): return "PLACEHOLDER"
    if len(key) < 8: return "***"
    return f"{key[:4]}...{key[-4:]}"

print(f"DEBUG: SUPABASE_URL: {SUPABASE_URL}")
print(f"DEBUG: SUPABASE_KEY: {mask_key(SUPABASE_KEY)}")
print(f"DEBUG: BREVO_KEY: {mask_key(BREVO_KEY)}")
print(f"DEBUG: SENDER_EMAIL: {SENDER_EMAIL}")
print(f"DEBUG: GEMINI_API_KEY: {mask_key(GEMINI_API_KEY)}")

# Safe Initialization
supabase: Optional[Client] = None

def get_supabase_client():
    global supabase
    if supabase:
        return supabase
    
    url = get_env_robust(["SUPABASE_URL", "VITE_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"])
    key = get_env_robust([
        "SUPABASE_ANON_KEY", "VITE_SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_KEY", "SUPABASE_SERVICE_ROLE_KEY"
    ])
    
    if url and key:
        try:
            supabase = create_client(url, key)
            return supabase
        except Exception as e:
            print(f"Supabase Init Error: {e}")
    return None

# Initial attempt
get_supabase_client()

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
    # Re-read env vars to catch changes without restart if possible
    # Note: os.environ is updated if the process environment changes, 
    # but usually a full restart is needed for AI Studio settings.
    
    current_supabase_url = get_env_robust(["SUPABASE_URL", "VITE_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"])
    current_supabase_key = get_env_robust([
        "SUPABASE_ANON_KEY", "VITE_SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_KEY", "SUPABASE_SERVICE_ROLE_KEY"
    ])
    current_brevo_key = get_env_robust(["BREVO_API_KEY", "VITE_BREVO_API_KEY", "SENDINBLUE_API_KEY"])
    current_sender_email = get_env_robust(["SENDER_EMAIL", "VITE_SENDER_EMAIL", "BREVO_SENDER_EMAIL"])
    current_gemini_key = get_env_robust(["GEMINI_API_KEY", "VITE_GEMINI_API_KEY", "GOOGLE_API_KEY", "API_KEY"])

    return {
        "status": "online",
        "supabase": current_supabase_url is not None and current_supabase_key is not None,
        "brevo": current_brevo_key is not None and current_sender_email is not None,
        "gemini": current_gemini_key is not None,
        "env_vars": {
            "SUPABASE_URL": current_supabase_url is not None,
            "SUPABASE_ANON_KEY": current_supabase_key is not None,
            "BREVO_API_KEY": current_brevo_key is not None,
            "SENDER_EMAIL": current_sender_email is not None,
            "GEMINI_API_KEY": current_gemini_key is not None,
        },
        "masked_vars": {
            "SUPABASE_URL": current_supabase_url if current_supabase_url else "MISSING",
            "SUPABASE_ANON_KEY": mask_key(current_supabase_key),
            "BREVO_API_KEY": mask_key(current_brevo_key),
            "SENDER_EMAIL": current_sender_email if current_sender_email else "MISSING",
            "GEMINI_API_KEY": mask_key(current_gemini_key),
        },
        "all_env_keys": sorted(list(os.environ.keys())),
        "env_file_exists": os.path.exists(os.path.join(os.getcwd(), ".env")),
        "api_ready": True
    }

@app.get("/api/tasks")
async def list_tasks():
    client = get_supabase_client()
    if not client: 
        print("Supabase client not initialized")
        return []
    try:
        res = client.table("tasks").select("*").order("date").execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Supabase Select Error: {e}")
        # If it's a 401, it might be an invalid key
        if "401" in str(e) or "Unauthorized" in str(e):
            raise HTTPException(status_code=401, detail=f"Supabase Authorization Error: {str(e)}")
        return []

@app.post("/api/tasks")
async def add_task(task: TaskItem):
    client = get_supabase_client()
    if not client: raise HTTPException(status_code=503, detail="Database connection not initialized")
    try:
        data = task.dict(exclude_none=True)
        if 'id' in data: del data['id']
        res = client.table("tasks").insert(data).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/tasks/{task_id}/toggle")
async def toggle(task_id: str):
    client = get_supabase_client()
    if not client: raise HTTPException(status_code=503, detail="Database offline")
    try:
        res = client.table("tasks").select("completed").eq("id", task_id).execute()
        if not res.data: raise HTTPException(status_code=404, detail="Task not found")
        new_val = not res.data[0]['completed']
        client.table("tasks").update({"completed": new_val}).eq("id", task_id).execute()
        return {"status": "ok", "completed": new_val}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def remove_task(task_id: str):
    client = get_supabase_client()
    if not client: raise HTTPException(status_code=503, detail="Database offline")
    try:
        client.table("tasks").delete().eq("id", task_id).execute()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
async def save_settings(settings: UserSettings):
    client = get_supabase_client()
    if not client: raise HTTPException(status_code=503, detail="Database offline")
    try:
        # We use a fixed ID for single user settings for now
        res = client.table("settings").upsert({
            "id": "main_user",
            "email": settings.email,
            "name": settings.name
        }).execute()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
async def get_settings():
    client = get_supabase_client()
    if not client: return {"email": "", "name": "Zen User"}
    try:
        res = client.table("settings").select("*").eq("id", "main_user").execute()
        if res.data:
            return res.data[0]
        return {"email": "", "name": "Zen User"}
    except Exception as e:
        return {"email": "", "name": "Zen User"}

@app.get("/api/cron")
async def daily_cron_trigger():
    client = get_supabase_client()
    if not client: return {"error": "Database offline"}
    try:
        # 1. Get User Settings
        settings_res = client.table("settings").select("*").eq("id", "main_user").execute()
        if not settings_res.data:
            return {"error": "No user settings found. Please configure your email in the app."}
        
        user_email = settings_res.data[0]['email']
        user_name = settings_res.data[0].get('name', 'Zen User')

        # 2. Get Today's Tasks
        today = datetime.date.today().isoformat()
        res = client.table("tasks").select("*").eq("date", today).eq("completed", False).execute()
        
        # 3. Generate AI Briefing
        briefing_html = await generate_gemini_briefing(res.data, user_name)
        
        # 4. Send Email
        email_status = await send_email_via_api(user_email, "Your MorningZen Briefing", briefing_html)
        
        return {"status": "processed", "email": email_status, "tasks_found": len(res.data)}
    except Exception as e:
        return {"error": str(e)}
