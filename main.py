from fastapi import FastAPI, HTTPException, status, Response
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

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

@app.get("/")
def get_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def get_health():
    return {"status": "ok"}

@app.get("/tasks")
def get_all_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_single_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
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

@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
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

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
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