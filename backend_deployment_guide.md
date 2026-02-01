
# Deploying Your MorningZen System for Free

To fulfill the "years without disturbance" requirement, follow this architecture:

## 1. Backend (FastAPI)
Deploy a FastAPI server to **Render** or **Railway** (free tiers).
- Use `APScheduler` to run a job daily.
- The job should query Supabase for users who have a "preferredMorningTime" matching the current hour.
- Send a request to Gemini (or use your internal logic) to get the briefing text.
- Use the **Brevo API** to send the email.

## 2. Database (Supabase)
- Create a `tasks` table and a `settings` table.
- Use the Supabase Free Tier (PostgreSQL). It will run forever as long as there is some activity every few months.

## 3. Email (Brevo)
- Sign up for a free account.
- Get your API Key.
- You get 300 emails/day for free, which is perfect for personal use.

## 4. Example FastAPI Cron Job Code
```python
from apscheduler.schedulers.background import BackgroundScheduler
import requests

def send_daily_briefing():
    # 1. Fetch users from Supabase
    # 2. For each user, fetch today's tasks
    # 3. Generate content with Gemini
    # 4. Send via Brevo
    print("Briefing sent!")

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_briefing, 'cron', hour=8, minute=0)
scheduler.start()
```

## 5. Frontend (React)
- Deploy this application to **Vercel** or **Netlify** (Free).
- It communicates with your FastAPI backend endpoints for persistence.
