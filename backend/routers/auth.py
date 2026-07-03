from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from models.mongo_models import get_db, User
from routers.auth_utils import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register_user(request: RegisterRequest):
    db = await get_db()
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        name=request.name
    )
    result = await db.users.insert_one(user.model_dump(by_alias=True, exclude_none=True))
    
    access_token = create_access_token(data={"sub": str(result.inserted_id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": str(result.inserted_id), "name": user.name, "email": user.email, "role": user.role}
    }

@router.post("/login")
async def login_user(request: LoginRequest):
    db = await get_db()
    user_dict = await db.users.find_one({"email": request.email})
    if not user_dict or not verify_password(request.password, user_dict["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user_dict["_id"])})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": str(user_dict["_id"]), "name": user_dict["name"], "email": user_dict["email"], "role": user_dict.get("role", "manager")}
    }
