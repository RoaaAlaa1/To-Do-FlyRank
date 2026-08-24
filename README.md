# Task API

A simple in-memory CRUD API for managing tasks, built with FastAPI.

## Setup

```bash
pip install fastapi uvicorn
```

## Run

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Documentation

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

- `GET /` - API metadata
- `GET /health` - Health check
- `GET /tasks` - List all tasks
- `GET /tasks/{task_id}` - Get one task
- `POST /tasks` - Create a task
- `PUT /tasks/{task_id}` - Update a task
- `DELETE /tasks/{task_id}` - Delete a task

## Screenshot of the UI 
![Description of image](images/Screenshot.png)
Example request:

```bash
curl -X POST "http://127.0.0.1:8000/tasks" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Learn FastAPI\"}"
```

> Tasks are stored in memory and reset whenever the application restarts.
