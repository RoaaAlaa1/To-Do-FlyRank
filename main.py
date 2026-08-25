import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Response
from pydantic import BaseModel
from typing import Optional

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")

def get_db_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                );
            """)
            cur.execute("SELECT COUNT(*) FROM tasks;")
            count = cur.fetchone()["count"]
            if count == 0:
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                    [
                        ("Buy groceries", False),
                        ("Read a book", True),
                        ("Write code", False)
                    ]
                )
            conn.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Task API", version="3.0", lifespan=lifespan)

@app.get("/")
def get_root():
    return {"name": "Task API", "version": "3.0", "endpoints": ["/tasks"]}

@app.get("/health")
def get_health():
    return {"status": "ok"}

@app.get("/tasks", summary="List all tasks")
def get_all_tasks():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks ORDER BY id ASC;")
            return cur.fetchall()

@app.get("/tasks/{task_id}", summary="Get single task")
def get_single_task(task_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
            task = cur.fetchone()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            return task

class TaskCreate(BaseModel):
    title: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.post("/tasks", status_code=status.HTTP_201_CREATED, summary="Create task")
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")

    clean_title = payload.title.strip()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;",
                (clean_title, False)
            )
            new_task = cur.fetchone()
            conn.commit()
            return new_task

@app.put("/tasks/{task_id}", summary="Update task")
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            new_title = current["title"]
            new_done = current["done"]

            if payload.title is not None:
                if not payload.title.strip():
                    raise HTTPException(status_code=400, detail="Title cannot be empty")
                new_title = payload.title.strip()

            if payload.done is not None:
                new_done = payload.done

            cur.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done;",
                (new_title, new_done, task_id)
            )
            updated_task = cur.fetchone()
            conn.commit()
            return updated_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete task")
def delete_task(task_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            conn.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)