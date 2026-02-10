"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = [
    {"id": 1, "name": "Basketball", "category": "sports", "participants": []},
    {"id": 2, "name": "Painting Workshop", "category": "artistic", "participants": []},
    {"id": 3, "name": "Python Bootcamp", "category": "intellectual", "participants": []},
    {"id": 4, "name": "Tennis Tournament", "category": "sports", "participants": []},
    {"id": 5, "name": "Swimming Competition", "category": "sports", "participants": []},
    {"id": 6, "name": "Dance Class", "category": "artistic", "participants": []},
    {"id": 7, "name": "Sculpture Studio", "category": "artistic", "participants": []},
    {"id": 8, "name": "Machine Learning Seminar", "category": "intellectual", "participants": []},
    {"id": 9, "name": "Chess Tournament", "category": "intellectual", "participants": []},
]


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in activities[activity_name]["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up for this activity")

    # Get the specific activity
    activity = activities[activity_name]

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}
