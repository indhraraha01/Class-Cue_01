from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Dict, Any
import uuid
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# Authentication (JWT bearer tokens + bcrypt password hashing)
# ---------------------------------------------------------------------------
JWT_ALGORITHM = "HS256"
TOKEN_TTL_DAYS = 7


def _jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": payload.get("sub")}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


class SignupInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


def _public_user(user: dict) -> dict:
    return {"id": user["id"], "email": user["email"], "name": user.get("name", "")}


@api_router.post("/auth/signup")
async def signup(payload: SignupInput):
    email = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "name": payload.name.strip(),
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user)
    token = create_access_token(user["id"], user["email"])
    return {"token": token, "user": _public_user(user)}


@api_router.post("/auth/login")
async def login(payload: LoginInput):
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_access_token(user["id"], user["email"])
    return {"token": token, "user": _public_user(user)}


@api_router.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    return _public_user(current_user)



# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class AppState(BaseModel):
    model_config = ConfigDict(extra="ignore")
    subjects: List[Dict[str, Any]] = []
    students: List[Dict[str, Any]] = []
    sessions: List[Dict[str, Any]] = []
    lessons: List[Dict[str, Any]] = []
    attendance: List[Dict[str, Any]] = []
    assignments: List[Dict[str, Any]] = []
    grades: List[Dict[str, Any]] = []
    notes: List[Dict[str, Any]] = []

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Class Cue API"}

@api_router.get("/state", response_model=AppState)
async def get_state(current_user: dict = Depends(get_current_user)):
    doc = await db.user_states.find_one({"user_id": current_user["id"]}, {"_id": 0, "user_id": 0})
    if doc:
        return doc
    return AppState().model_dump()

@api_router.put("/state", response_model=AppState)
async def save_state(state: AppState, current_user: dict = Depends(get_current_user)):
    data = state.model_dump()
    await db.user_states.replace_one(
        {"user_id": current_user["id"]},
        {"user_id": current_user["id"], **data},
        upsert=True,
    )
    return data

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def ensure_indexes():
    try:
        await db.users.create_index("email", unique=True)
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not create users.email index: %s", exc)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()