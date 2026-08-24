import sqlite3
from fastapi import FastAPI, HTTPException, status, Response
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional

DB_FILE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create table if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    # 2. Seed only if empty
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Buy groceries", 0),
                ("Read a book", 1),
                ("Write code", 0)
            ]
        )
        conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Task API",
    description="SQLite-backed CRUD API",
    version="2.0",
    lifespan=lifespan
)

class TaskCreate(BaseModel):
    title: Optional[str] = None

@app.post("/tasks", status_code=status.HTTP_201_CREATED, summary="Create task")
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Title is required and cannot be empty"
        )
    
    clean_title = payload.title.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (clean_title, 0))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return {"id": new_id, "title": clean_title, "done": False}

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.put("/tasks/{task_id}", summary="Update task")
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="At least one field (title or done) must be provided"
        )
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    new_title = row["title"]
    new_done = row["done"]
    
    if payload.title is not None:
        if not payload.title.strip():
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Title cannot be empty"
            )
        new_title = payload.title.strip()
        
    if payload.done is not None:
        new_done = 1 if payload.done else 0
        
    cursor.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?", 
        (new_title, new_done, task_id)
    )
    conn.commit()
    conn.close()
    
    return {"id": task_id, "title": new_title, "done": bool(new_done)}

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete task")
def delete_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/")
def get_root():
    return {
        "name": "Task API",
        "version": "2.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def get_health():
    return {"status": "ok"}

@app.get("/tasks", summary="List all tasks")
def get_all_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]

@app.get("/tasks/{task_id}", summary="Get single task")
def get_single_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}