
# FastAPI + Supabase Integration Guide

To connect your **MorningZen** frontend to your permanent backend, your FastAPI app should expose the following endpoints.

### 1. Requirements
Install these dependencies:
```bash
pip install fastapi uvicorn supabase apscheduler pydantic sendinblue
```

### 2. FastAPI Core Structure (`main.py`)
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase import create_client, Client
import os

app = FastAPI()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

class TaskSchema(BaseModel):
    title: str
    description: Optional[str] = ""
    date: str
    priority: str
    completed: bool = False

@app.get("/tasks", response_model=List[TaskSchema])
async def get_tasks():
    # Fetch from Supabase
    response = supabase.table("tasks").select("*").execute()
    return response.data

@app.post("/tasks")
async def create_task(task: TaskSchema):
    # Insert into Supabase
    data, count = supabase.table("tasks").insert(task.dict()).execute()
    return data[1][0] # Return the created task

@app.patch("/tasks/{task_id}/toggle")
async def toggle_task(task_id: str):
    # Get current state and flip it
    res = supabase.table("tasks").select("completed").eq("id", task_id).execute()
    new_state = not res.data[0]['completed']
    supabase.table("tasks").update({"completed": new_state}).eq("id", task_id).execute()
    return {"status": "success"}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    supabase.table("tasks").delete().eq("id", task_id).execute()
    return {"status": "deleted"}
```

### 3. Deploying for "Years of No Disturbance"
- **Render.com**: Connect your GitHub. It will automatically build and deploy.
- **Supabase**: Set up a free project. Use the "Project Settings" to find your URL and API Keys.
- **Environment Variables**: Make sure to set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `GEMINI_API_KEY` in your Render dashboard.
