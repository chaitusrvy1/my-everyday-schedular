
import os
import datetime
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from apscheduler.schedulers.background import BackgroundScheduler
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import google.generativeai as genai

app = FastAPI(title="MorningZen Backend")

# CORS Configuration for Frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
GEMINI_KEY = os.environ.get("API_KEY")
BREVO_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "morning@zen.app")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_KEY)

# Data Models
class Task(BaseModel):
    id: Optional[str]
    title: str
    description: Optional[str] = ""
    date: str
    priority: str
    completed: bool = False

class UserSettings(BaseModel):
    email: str
    preferredMorningTime: str # "HH:MM"

# --- Email Logic ---
def send_email(to_email: str, subject: str, html_content: str):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email}],
        sender={"email": SENDER_EMAIL, "name": "MorningZen"},
        subject=subject,
        html_content=html_content
    )
    try:
        api_instance.send_trans_email(send_smtp_email)
        print(f"Email sent to {to_email}")
    except ApiException as e:
        print(f"Exception when calling Brevo: {e}")

# --- AI Briefing Generator (Python) ---
def generate_ai_briefing(tasks: List[dict]):
    model = genai.GenerativeModel('gemini-1.5-flash')
    task_list = "\n".join([f"- {t['title']} ({t['priority']})" for t in tasks])
    prompt = f"Generate a high-energy morning briefing. Include a quote, a motivational 2-sentence intro, and advice on these tasks:\n{task_list}"
    response = model.generate_content(prompt)
    return response.text

# --- Scheduled Job ---
def check_and_send_briefings():
    now = datetime.datetime.now().strftime("%H:%M")
    # Fetch user settings (assuming single user for simplicity, or iterate)
    res = supabase.table("settings").select("*").eq("preferredMorningTime", now).execute()
    for user in res.data:
        email = user['email']
        today = datetime.date.today().isoformat()
        # Fetch today's tasks
        task_res = supabase.table("tasks").select("*").eq("date", today).eq("completed", False).execute()
        briefing_text = generate_ai_briefing(task_res.data)
        
        html = f"""
        <h1>Good Morning!</h1>
        <p>{briefing_text.replace('\n', '<br>')}</p>
        <hr>
        <p>Go seize the day!</p>
        """
        send_email(email, "Your MorningZen Briefing", html)

scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_briefings, 'interval', minutes=1)
scheduler.start()

# --- API Endpoints ---
@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    res = supabase.table("tasks").select("*").order("createdAt", desc=True).execute()
    return res.data

@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    data = task.dict()
    if 'id' in data: del data['id']
    res = supabase.table("tasks").insert(data).execute()
    return res.data[0]

@app.patch("/tasks/{task_id}/toggle")
async def toggle_task(task_id: str):
    res = supabase.table("tasks").select("completed").eq("id", task_id).execute()
    if not res.data: raise HTTPException(status_code=404)
    new_status = not res.data[0]['completed']
    supabase.table("tasks").update({"completed": new_status}).eq("id", task_id).execute()
    return {"status": "success"}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    supabase.table("tasks").delete().eq("id", task_id).execute()
    return {"status": "deleted"}

@app.post("/settings")
async def save_settings(settings: UserSettings):
    # Upsert logic
    supabase.table("settings").upsert(settings.dict(), on_conflict="email").execute()
    return {"status": "saved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
