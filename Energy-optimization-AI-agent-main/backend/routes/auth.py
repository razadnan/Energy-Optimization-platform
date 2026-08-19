import hashlib
import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from backend.database import DatabaseManager

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Passwords helper
SALT = "energy_agent_salt_2026"

def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode('utf-8')).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# Request & Response Schemas
class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    organization: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class UserResponseSchema(BaseModel):
    id: int
    name: str
    email: str
    organization: str
    created_at: str


@router.post("/register", response_model=UserResponseSchema)
def register(user: RegisterSchema):
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email is already registered.")

        # Hash password and insert
        hashed = hash_password(user.password)
        created_at = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO users (name, email, password, organization, created_at) VALUES (?, ?, ?, ?, ?)",
            (user.name, user.email, hashed, user.organization, created_at)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "organization": user.organization,
            "created_at": created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


@router.post("/login", response_model=UserResponseSchema)
def login(credentials: LoginSchema):
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, email, password, organization, created_at FROM users WHERE email = ?", (credentials.email,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
            
        user_id, name, email, hashed_pw, organization, created_at = row
        if not verify_password(credentials.password, hashed_pw):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
            
        return {
            "id": user_id,
            "name": name,
            "email": email,
            "organization": organization,
            "created_at": created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
