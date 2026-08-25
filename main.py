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

