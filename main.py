from fastapi import FastAPI, HTTPException, status, Response
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Task API",
    description="A lightweight in-memory CRUD API for managing tasks.",
    version="1.0"
)

tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Write code", "done": False}
]

class TaskCreate(BaseModel):
    title: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/", summary="Root metadata")
def get_root():
    """Returns basic API info and available endpoints."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health", summary="Health check")
def get_health():
    """Endpoint for monitoring service status."""
    return {"status": "ok"}

@app.get("/tasks", summary="List all tasks")
def get_all_tasks():
    """Fetch all tasks currently stored in memory."""
    return tasks

@app.get("/tasks/{task_id}", summary="Get single task")
def get_single_task(task_id: int):
    """Retrieve a task by its unique numeric ID."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.post("/tasks", status_code=status.HTTP_201_CREATED, summary="Create task")
def create_task(payload: TaskCreate):
    """Create a new task with a default done status of false."""
    if not payload.title or not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Title is required and cannot be empty"
        )
    
    next_id = max([t["id"] for t in tasks], default=0) + 1
    new_task = {
        "id": next_id,
        "title": payload.title.strip(),
        "done": False
    }
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{task_id}", summary="Update task")
def update_task(task_id: int, payload: TaskUpdate):
    """Update a task's title and/or completion state."""
    target_task = None
    for task in tasks:
        if task["id"] == task_id:
            target_task = task
            break
            
    if not target_task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    if payload.title is None and payload.done is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="At least one field (title or done) must be provided"
        )
        
    if payload.title is not None:
        if not payload.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Title cannot be empty"
            )
        target_task["title"] = payload.title.strip()
        
    if payload.done is not None:
        target_task["done"] = payload.done
        
    return target_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete task")
def delete_task(task_id: int):
    """Remove a task by ID."""
    global tasks
    target_task = None
    for task in tasks:
        if task["id"] == task_id:
            target_task = task
            break
            
    if not target_task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    tasks = [t for t in tasks if t["id"] != task_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)