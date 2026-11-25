import uuid
from typing import Dict, List, Optional

import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Institute 360 REST API",
    version="1.0.0",
    description="Student CRUD + Chatbot REST API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Schemas ----------
class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str


class StudentIn(BaseModel):
    name: str
    email: str
    course: str
    age: Optional[int] = None


class Student(StudentIn):
    id: int


# ---------- Local Qwen via Ollama ----------
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"  # other installed option: qwen2.5:1.5b (faster, less accurate)
SYSTEM_PROMPT = (
    "You are the Institute 360 AI Assistant. Answer any general question "
    "clearly and helpfully. For institute topics (courses, fees, exams, "
    "placements), help as best you can and say if you are unsure."
)

# ---------- In-memory storage ----------
conversations: Dict[str, List[dict]] = {}
students_db: Dict[int, Student] = {}
next_id = 1


# ---------- Home ----------
@app.get("/")
def home():
    return {
        "message": "Welcome to Institute 360 API!",
        "status": "Running",
    }


# ---------- Chat ----------
@app.post("/api/chat")
def chat(request: ChatRequest):
    conv_id = request.conversation_id or str(uuid.uuid4())
    history = conversations.setdefault(conv_id, [])
    history.append({"role": "user", "content": request.message})
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}]
                + history[-20:],
                "stream": False,
            },
            timeout=300,
        )
        r.raise_for_status()
        reply = r.json()["message"]["content"]
    except Exception as e:
        history.pop()
        raise HTTPException(status_code=500, detail=f"Qwen error: {e}")
    history.append({"role": "assistant", "content": reply})
    return {
        "conversation_id": conv_id,
        "user_message": request.message,
        "reply": reply,
    }


# ---------- Student CRUD ----------
@app.get("/students")
def get_students():
    return list(students_db.values())


@app.post("/students")
def add_student(student: StudentIn):
    global next_id
    new_student = Student(id=next_id, **student.model_dump())
    students_db[next_id] = new_student
    next_id += 1
    return new_student


@app.get("/students/{student_id}")
def get_student(student_id: int):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    return students_db[student_id]


@app.put("/students/{student_id}")
def update_student(student_id: int, student: StudentIn):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    students_db[student_id] = Student(id=student_id, **student.model_dump())
    return students_db[student_id]


@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    del students_db[student_id]
    return {"message": f"Student {student_id} deleted"}