
import os
import datetime
import httpx
import random
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    # Also check for lowercase versions and common variations
    all_keys = []
    for k in keys:
        all_keys.append(k)
        all_keys.append(k.lower())
        if not k.startswith("VITE_"):
            all_keys.append(f"VITE_{k}")
        if not k.startswith("NEXT_PUBLIC_"):
            all_keys.append(f"NEXT_PUBLIC_{k}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keys = [x for x in all_keys if not (x in seen or seen.add(x))]

    for key in unique_keys:
        val = os.environ.get(key)
        if val and not is_placeholder(val):
            # Strip quotes if present (common issue when copying from .env files)
            val = val.strip().strip("'").strip('"')
            if val:
                return val
    return None

SUPABASE_URL_KEYS = ["SUPABASE_URL", "VITE_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_PROJECT_URL"]
SUPABASE_KEY_KEYS = [
    "SUPABASE_ANON_KEY", "VITE_SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY"
]
BREVO_KEY_KEYS = ["BREVO_API_KEY", "VITE_BREVO_API_KEY", "SENDINBLUE_API_KEY", "BREVO_KEY"]
SENDER_EMAIL_KEYS = ["SENDER_EMAIL", "VITE_SENDER_EMAIL", "BREVO_SENDER_EMAIL", "BREVO_SENDER"]
GEMINI_API_KEY_KEYS = ["GEMINI_API_KEY", "VITE_GEMINI_API_KEY", "GOOGLE_API_KEY", "API_KEY", "GEMINI_KEY"]

def get_supabase_config():
    url = get_env_robust(SUPABASE_URL_KEYS)
    key = get_env_robust(SUPABASE_KEY_KEYS)
    if url and url.endswith("/"):
        url = url[:-1]
    return url, key

def get_supabase_headers(key):
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

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

# Safe Initialization

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

async def generate_gemini_briefing(tasks: List[dict], user_name: str, api_key: str):
    """Generates a personalized briefing using Gemini AI."""
    if not api_key:
        return "Gemini API key missing. Please configure it in environment variables."
    
    client = genai.Client(api_key=api_key)
    
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

async def send_email_via_api(to_email: str, subject: str, content: str, api_key: str, sender: str):
    """Sends email using Brevo REST API directly."""
    if not api_key or not sender:
        return "Email configuration missing (BREVO_KEY or SENDER_EMAIL)."
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "MorningZen", "email": sender},
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
    url, key = get_supabase_config()
    brevo_key = get_env_robust(BREVO_KEY_KEYS)
    sender_email = get_env_robust(SENDER_EMAIL_KEYS)
    gemini_key = get_env_robust(GEMINI_API_KEY_KEYS)

    supabase_status = "Missing Config"
    if url and key:
        try:
            async with httpx.AsyncClient() as client:
                headers = get_supabase_headers(key)
                # Try to hit the root of the rest api
                r = await client.get(f"{url}/rest/v1/", headers=headers, timeout=5.0)
                if r.status_code == 200:
                    supabase_status = "Connected"
                else:
                    supabase_status = f"Error {r.status_code}: {r.text[:100]}"
        except Exception as e:
            supabase_status = f"Exception: {str(e)}"

    return {
        "status": "online",
        "supabase_connection": supabase_status,
        "supabase": url is not None and key is not None,
        "brevo": brevo_key is not None and sender_email is not None,
        "gemini": gemini_key is not None,
        "env_vars": {
            "SUPABASE_URL": url is not None,
            "SUPABASE_ANON_KEY": key is not None,
            "BREVO_API_KEY": brevo_key is not None,
            "SENDER_EMAIL": sender_email is not None,
            "GEMINI_API_KEY": gemini_key is not None,
        },
        "masked_vars": {
            "SUPABASE_URL": url if url else "MISSING",
            "SUPABASE_ANON_KEY": mask_key(key),
            "BREVO_API_KEY": mask_key(brevo_key),
            "SENDER_EMAIL": sender_email if sender_email else "MISSING",
            "GEMINI_API_KEY": mask_key(gemini_key),
        },
        "all_env_keys": sorted(list(os.environ.keys())),
        "env_file_exists": os.path.exists(os.path.join(os.getcwd(), ".env")),
        "api_ready": True
    }

@app.get("/api/tasks")
async def list_tasks():
    url, key = get_supabase_config()
    if not url or not key:
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            headers = get_supabase_headers(key)
            res = await client.get(f"{url}/rest/v1/tasks?select=*&order=date", headers=headers)
            if res.status_code == 200:
                return res.json()
            else:
                print(f"Supabase Error {res.status_code}: {res.text}")
                if res.status_code == 401:
                    raise HTTPException(status_code=401, detail=res.text)
                return []
    except HTTPException:
        raise
    except Exception as e:
        print(f"Supabase Select Error: {e}")
        return []

@app.post("/api/tasks")
async def add_task(task: TaskItem):
    url, key = get_supabase_config()
    if not url or not key:
        raise HTTPException(status_code=503, detail="Database config missing")
    
    try:
        data = task.dict(exclude_none=True)
        if 'id' in data: del data['id']
        
        async with httpx.AsyncClient() as client:
            headers = get_supabase_headers(key)
            res = await client.post(f"{url}/rest/v1/tasks", headers=headers, json=data)
            if res.status_code in [200, 201]:
                return res.json()[0]
            else:
                raise HTTPException(status_code=res.status_code, detail=res.text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/tasks/{task_id}/toggle")
async def toggle(task_id: str):
    url, key = get_supabase_config()
    if not url or not key:
        raise HTTPException(status_code=503, detail="Database offline")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = get_supabase_headers(key)
            # 1. Get current state
            res = await client.get(f"{url}/rest/v1/tasks?select=completed&id=eq.{task_id}", headers=headers)
            if not res.json():
                raise HTTPException(status_code=404, detail="Task not found")
            
            new_val = not res.json()[0]['completed']
            
            # 2. Update
            update_res = await client.patch(
                f"{url}/rest/v1/tasks?id=eq.{task_id}", 
                headers=headers, 
                json={"completed": new_val}
            )
            return {"status": "ok", "completed": new_val}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tasks/{task_id}")
async def remove_task(task_id: str):
    url, key = get_supabase_config()
    if not url or not key:
        raise HTTPException(status_code=503, detail="Database offline")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = get_supabase_headers(key)
            await client.delete(f"{url}/rest/v1/tasks?id=eq.{task_id}", headers=headers)
            return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
async def save_settings(settings: UserSettings):
    url, key = get_supabase_config()
    if not url or not key:
        raise HTTPException(status_code=503, detail="Database offline")
    
    try:
        data = {
            "id": "main_user",
            "email": settings.email,
            "name": settings.name
        }
        async with httpx.AsyncClient() as client:
            headers = get_supabase_headers(key)
            # Upsert logic: try to update, if not found, insert
            # In PostgREST, we can use Prefer: resolution=merge-duplicates
            headers["Prefer"] = "return=representation,resolution=merge-duplicates"
            res = await client.post(f"{url}/rest/v1/settings", headers=headers, json=data)
            return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
async def get_settings():
    url, key = get_supabase_config()
    if not url or not key:
        return {"email": "", "name": "Zen User"}
    
    try:
        async with httpx.AsyncClient() as client:
            headers = get_supabase_headers(key)
            res = await client.get(f"{url}/rest/v1/settings?select=*&id=eq.main_user", headers=headers)
            data = res.json()
            if data:
                return data[0]
            return {"email": "", "name": "Zen User"}
    except Exception as e:
        return {"email": "", "name": "Zen User"}

@app.get("/api/cron")
async def daily_cron_trigger():
    url, key = get_supabase_config()
    if not url or not key:
        return {"error": "Database offline"}
    
    try:
        async with httpx.AsyncClient() as client:
            headers = get_supabase_headers(key)
            
            # 1. Get User Settings
            settings_res = await client.get(f"{url}/rest/v1/settings?select=*&id=eq.main_user", headers=headers)
            settings_data = settings_res.json()
            if not settings_data:
                return {"error": "No user settings found. Please configure your email in the app."}
            
            user_email = settings_data[0]['email']
            user_name = settings_data[0].get('name', 'Zen User')

            # 2. Get Today's Tasks
            today = datetime.date.today().isoformat()
            tasks_res = await client.get(f"{url}/rest/v1/tasks?select=*&date=eq.{today}&completed=eq.false", headers=headers)
            tasks_data = tasks_res.json()
            
            # 3. Generate AI Briefing
            gemini_key = get_env_robust(GEMINI_API_KEY_KEYS)
            briefing_html = await generate_gemini_briefing(tasks_data, user_name, gemini_key)
            
            # 4. Send Email
            brevo_key = get_env_robust(BREVO_KEY_KEYS)
            sender_email = get_env_robust(SENDER_EMAIL_KEYS)
            email_status = await send_email_via_api(user_email, "Your MorningZen Briefing", briefing_html, brevo_key, sender_email)
            
            return {"status": "processed", "email": email_status, "tasks_found": len(tasks_data)}
    except Exception as e:
        return {"error": str(e)}
