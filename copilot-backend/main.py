import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from database import get_db_connection

# Configure Gemini API
genai.configure(api_key=os.getenv("AQ.Ab8RN6KTeM9i3lvN-VzmL0JH3hxsSWUztb_phAHgmYxhDVzxAQ"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RoadmapRequest(BaseModel):
    user_id: int
    topic: str
    days: int
    hours_per_day: int

@app.post("/generate-roadmap")
def generate_roadmap(request: RoadmapRequest):
    try:
        # 1. Call Gemini AI to produce structured JSON
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
        Create a detailed study roadmap to learn '{request.topic}' over {request.days} days, spending {request.hours_per_day} hours/day.
        Return strictly a raw JSON object with NO markdown or code fences:
        {{
            "topic": "{request.topic}",
            "tasks": [
                {{"title": "Specific step or module title", "duration_minutes": 60}}
            ]
        }}
        """
        response = model.generate_content(prompt)
        
        # Clean response
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        plan_data = json.loads(clean_text)

        # 2. Persist in MySQL Database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Updated to match actual schema: goal_title and duration_days
        cursor.execute(
            "INSERT INTO study_plans (user_id, topic, goal_title, duration_days) VALUES (%s, %s, %s, %s)",
            (request.user_id, request.topic, request.topic, request.days)
        )
        plan_id = cursor.lastrowid

        for idx, task in enumerate(plan_data.get("tasks", []), start=1):
            cursor.execute(
                "INSERT INTO tasks (plan_id, day_number, task_description, is_completed) VALUES (%s, %s, %s, %s)",
                (plan_id, idx, task["title"], False)
            )
        
        conn.commit()
        cursor.close()
        conn.close()

        plan_data["plan_id"] = plan_id
        return plan_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TaskUpdate(BaseModel):
    is_completed: bool

@app.put("/tasks/{task_id}")
def update_task_status(task_id: int, payload: TaskUpdate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET is_completed = %s WHERE task_id = %s",
            (payload.is_completed, task_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "task_id": task_id, "is_completed": payload.is_completed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))