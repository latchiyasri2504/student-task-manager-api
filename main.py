
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from fastapi import Depends, FastAPI, HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text,
    URL, create_engine, or_
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session
from sqlalchemy.orm import mapped_column, sessionmaker


# 1. DATABASE CONNECTION
DB_USER = "postgres"
DB_PASSWORD = "4550"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "task_manager_db"

DATABASE_URL = URL.create(
    "postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


# 2. DATABASE TABLES
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )
    email: Mapped[str] = mapped_column(
        String(120), unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


Base.metadata.create_all(bind=engine)


# 3. FASTAPI AND SECURITY
app = FastAPI(title="Student Task Manager API")

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "QyNO2i7VhS4fR-a7JimzuCyvBMWA2SQdKdJfYePFdrA"
ALGORITHM = "HS256"
TOKEN_MINUTES = 30


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_token(username: str):
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=TOKEN_MINUTES
    )
    return jwt.encode(
        {"sub": username, "exp": expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    error = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username = payload.get("sub")
        if not username:
            raise error
    except InvalidTokenError:
        raise error

    user = db.query(User).filter(
        User.username == username
    ).first()

    if user is None:
        raise error
    return user


# 4. REQUEST / RESPONSE SCHEMAS
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str


class TaskCreate(BaseModel):
    title: str
    description: str = ""


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    completed: bool
    user_id: int
    created_at: datetime


# 5. HOME
@app.get("/")
def home():
    return {"message": "Student Task Manager API is running"}


# 6. REGISTER
@app.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        or_(User.username == data.username, User.email == data.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered",
        )

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=password_hash.hash(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# 7. LOGIN
@app.post("/login", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.username == form.username
    ).first()

    if user is None or not password_hash.verify(
        form.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    return {
        "access_token": create_token(user.username),
        "token_type": "bearer",
    }


# 8. PROFILE
@app.get("/profile", response_model=UserOut)
def profile(user: User = Depends(get_current_user)):
    return user


# 9. CREATE TASK
@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = Task(
        title=data.title,
        description=data.description,
        user_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# 10. READ ALL TASKS
@app.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Task).filter(Task.user_id == user.id).all()


# 11. READ ONE TASK
@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == user.id
    ).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# 12. UPDATE TASK
@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == user.id
    ).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in data.model_dump(
        exclude_unset=True, exclude_none=True
    ).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


# 13. DELETE TASK
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == user.id
    ).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return None
