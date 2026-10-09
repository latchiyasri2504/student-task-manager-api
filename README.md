
# Student Task Manager API

## Project Overview
This project is a REST API developed using FastAPI and PostgreSQL. It allows users to register, log in, and manage tasks using CRUD operations.

## Technologies Used
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT Authentication
- Swagger UI

## Features
- User registration
- User login
- JWT-based authentication
- View user profile
- Create, read, update, and delete tasks
- PostgreSQL database connectivity

## Installation

Install the required packages:

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
uvicorn main:app --reload
```

Open Swagger UI in your browser:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /register | Register a user |
| POST | /login | Log in |
| GET | /profile | View user profile |
| POST | /tasks | Create a task |
| GET | /tasks | View tasks |
| GET | /tasks/{task_id} | View one task |
| PUT | /tasks/{task_id} | Update a task |
| DELETE | /tasks/{task_id} | Delete a task |

## Database
PostgreSQL is used to store user and task information.

## Author
Latchiya Sri
  