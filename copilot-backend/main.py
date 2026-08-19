import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
from database import get_db_connection

# Load environment variables from your .env file
load_dotenv()

app = FastAPI(title="Smart AI Study Co-Pilot")

# Retrieve the API key string stored in the .env file
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from environment variables or .env file.")

# Initialize Gemini Client with the key
client = genai.Client(api_key=api_key)

class StudyPlanRequest(BaseModel):
    user_id: int
    goal: str
    days: int

@app.post("/generate-roadmap")
async def generate_roadmap(req: StudyPlanRequest):
    prompt = f"""
    Break down the following learning goal into a day-by-day task plan.
    Goal: {req.goal}
    Duration: {req.days} days.

    Return ONLY a valid JSON array of objects with keys "day" (integer) and "task" (string).
    Do not include any conversational text or markdown formatting outside the JSON array.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        tasks_data = json.loads(clean_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Processing Failed: {str(e)}")

    # Database Insertion Logic
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO study_plans (user_id, goal_title, duration_days) VALUES (%s, %s, %s)",
            (req.user_id, req.goal, req.days)
        )
        plan_id = cursor.lastrowid

        for item in tasks_data:
            cursor.execute(
                "INSERT INTO tasks (plan_id, day_number, task_description) VALUES (%s, %s, %s)",
                (plan_id, item["day"], item["task"])
            )
        
        conn.commit()
        return {"status": "success", "plan_id": plan_id, "tasks": tasks_data}
    
    except Exception as e:
        import traceback
        print("Detailed Error Traceback:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error details: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/get-plan/{plan_id}")
async def get_plan(plan_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM study_plans WHERE plan_id = %s", (plan_id,))
        plan = cursor.fetchone()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        cursor.execute("SELECT * FROM tasks WHERE plan_id = %s ORDER BY day_number ASC", (plan_id,))
        tasks = cursor.fetchall()
        
        return {"plan": plan, "tasks": tasks}
    finally:
        cursor.close()
        conn.close()