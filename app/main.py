from fastapi import FastAPI, HTTPException, Depends, Request, Response, Form, Cookie, APIRouter, status, Body
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware  # Changed from fastapi.middleware.base
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from urllib.parse import quote
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv
from app.llm_service.router import call_llm
from app.llm_service.groq import MODEL_PROVIDERS as GROQ_MODELS
from app.llm_service.gemini import MODEL_PROVIDERS as GEMINI_MODELS
from app.llm_service.deepseek import MODEL_PROVIDERS as DEEPSEEK_MODELS
from app.db.database import engine, get_db
from app.db import models, crud, init_db
from app.schemas import UserCreate, User, UserList, UserApproval, UserAdmin, UserActivation
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
import httpx
import os
import logging
import secrets
import time
import json
import asyncio
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Initialize FastAPI app
app = FastAPI(
    title="Chatbot API",
    description="FastAPI application for a chatbot with multiple LLM integrations",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Authentication middleware
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow access to public paths without authentication
        public_paths = ['/', '/login', '/register', '/token', '/static', '/health']
        path = request.url.path
        
        # Check if the path is public or starts with one of the public paths
        is_public = any(path == p or path.startswith(f"{p}/") for p in public_paths)
        
        if is_public:
            response = await call_next(request)
            return response
        
        # Check for authentication
        token = request.cookies.get("access_token")
        if not token:
            # For API requests that expect JSON
            if request.headers.get("accept") == "application/json":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated"}
                )
            # For regular browser requests, redirect to login
            return RedirectResponse(
                url=f"/login?redirect={quote(str(request.url.path))}",
                status_code=status.HTTP_302_FOUND
            )
        
        response = await call_next(request)
        return response

# Add the auth middleware
app.add_middleware(AuthMiddleware)

# Token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db, username=username)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Authentication dependency for routes
async def get_current_user_from_cookie(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = crud.get_user(db, username=username)
    if user is None or not user.is_active:
        return None
    
    return user

# API Authentication endpoints
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "is_admin": user.is_admin}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Initialize database on startup
@app.on_event("startup")
def startup_db_client():
    # Create database tables
    models.Base.metadata.create_all(bind=engine)
    
    # Initialize admin user
    db = next(get_db())
    init_db.init_db(db)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Page endpoints
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, current_user: Optional[models.User] = Depends(get_current_user_from_cookie)):
    error = request.query_params.get("error")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "is_authenticated": current_user is not None,
        "current_user": current_user,
        "username": current_user.username if current_user else None,
        "error": error
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, redirect: str = "/"):
    return templates.TemplateResponse("login.html", {"request": request, "redirect": redirect})

@app.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    redirect: str = Form("/"),
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, username, password)
    if not user:
        return RedirectResponse(
            url=f"/login?error=Invalid%20username%20or%20password&redirect={quote(redirect)}",
            status_code=303
        )
    
    # After authentication, check if the account is approved
    if not user.is_approved:
        return RedirectResponse(
            url=f"/login?error=Your%20account%20is%20pending%20approval%20by%20an%20administrator&redirect={quote(redirect)}",
            status_code=303
        )
    
    # Check if the account is suspended (inactive)
    if not user.is_active:
        return RedirectResponse(
            url=f"/login?error=Your%20account%20has%20been%20suspended.%20Please%20contact%20an%20administrator&redirect={quote(redirect)}",
            status_code=303
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "is_admin": user.is_admin}, 
        expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url=redirect, status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response

@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response

# User management endpoints (admin only)
@app.get("/api/admin/users", response_model=UserList)
async def read_users_api(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return {"users": users}

@app.get("/users/pending")
async def read_pending_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    users = crud.get_pending_users(db)
    return {"users": users}

@app.post("/users/approve")
async def approve_user(
    approval: UserApproval,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Get the current user from the cookie directly
        current_user = await get_current_user_from_cookie(request, Response(), db)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized. Admin privileges required.")
            
        if approval.approve:
            user = crud.approve_user(db, approval.user_id)
            if user:
                return {"message": f"User {user.username} approved successfully"}
            else:
                raise HTTPException(status_code=404, detail="User not found")
        return {"message": "No action taken"}
    except Exception as e:
        logger.error(f"Error approving user: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to approve user: {str(e)}")

@app.post("/users/admin")
async def set_admin_status(
    admin_status: UserAdmin,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        current_user = await get_current_user_from_cookie(request, Response(), db)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized. Admin privileges required.")
            
        if admin_status.make_admin:
            user = crud.promote_to_admin(db, admin_status.user_id)
            if user:
                return {"message": f"User {user.username} is now an admin"}
            else:
                raise HTTPException(status_code=404, detail="User not found")
        return {"message": "No action taken"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/activate")
async def set_active_status(
    activation: UserActivation,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        current_user = await get_current_user_from_cookie(request, Response(), db)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized. Admin privileges required.")
            
        if activation.activate:
            user = crud.activate_user(db, activation.user_id)
            action = "activated"
        else:
            user = crud.suspend_user(db, activation.user_id)
            action = "suspended"
        
        if user:
            return {"message": f"User {user.username} {action} successfully"}
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# User registration
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_user_form(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(None),
    email: str = Form(None),
    password: str = Form(None),
    user_json: Optional[UserCreate] = Body(None)
):
    # Handle API requests (JSON body)
    if user_json:
        try:
            existing_user = crud.get_user(db, username=user_json.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            
            new_user = crud.create_user(
                db=db,
                username=user_json.username,
                password=user_json.password,
                email=user_json.email,
                is_approved=False
            )
            
            if not new_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User registration failed"
                )
            
            return {"message": "User registered successfully. Please wait for admin approval."}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    # Handle form submissions
    try:
        if not username or not email or not password:
            return RedirectResponse(
                url="/register?error=All+fields+are+required",
                status_code=303
            )
            
        existing_user = crud.get_user(db, username=username)
        if existing_user:
            return RedirectResponse(
                url="/register?error=Username+already+registered",
                status_code=303
            )
        
        new_user = crud.create_user(
            db=db,
            username=username,
            password=password,
            email=email,
            is_approved=False
        )
        
        if not new_user:
            return RedirectResponse(
                url="/register?error=Registration+failed",
                status_code=303
            )
        
        return RedirectResponse(
            url="/register?success=true",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/register?error={str(e)}",
            status_code=303
        )

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login?redirect=%2Fadmin%2Fusers", status_code=303)
    
    if not current_user.is_admin:
        return RedirectResponse(url="/?error=Admin+access+required", status_code=303)
    
    users = crud.get_users(db)
    pending_users = crud.get_pending_users(db)
    message = request.query_params.get("message")
    
    return templates.TemplateResponse(
        "admin/users.html", 
        {
            "request": request,
            "users": users,
            "pending_users": pending_users,
            "current_user": current_user,
            "is_authenticated": True,
            "username": current_user.username,
            "message": message
        }
    )

# Chatbot and other endpoints
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(
    request: Request,
    current_user: Optional[models.User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        redirect_url = f"/login?redirect={quote('/chat')}"
        return RedirectResponse(url=redirect_url, status_code=303)
    
    model_options = get_model_options()
    selected_model = next(iter(GROQ_MODELS.keys()), "")
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "model_options": model_options,
            "selected_model": selected_model,
            "is_authenticated": True,
            "current_user": current_user,
            "username": current_user.username
        }
    )

@app.post("/chat")
async def chat(
    request: Request, 
    body: dict = Body(...),
    current_user: Optional[models.User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/?error=You%20need%20to%20login%20to%20access%20this%20page", status_code=303)
    
    try:
        messages = body.get("messages", [])
        model = body.get("model", list(GROQ_MODELS.keys())[0])
        max_tokens = body.get("max_tokens", 12800)
        stream = body.get("stream", False)
        # Ensure messages are dicts
        messages = [msg if isinstance(msg, dict) else msg.dict() for msg in messages]

        if stream:
            # Streaming response
            async def text_stream():
                llm_stream = await call_llm(messages, max_tokens, model)
                # If llm_stream is a generator, iterate and yield
                for chunk in llm_stream:
                    yield chunk
                    await asyncio.sleep(0)  # Yield control to event loop for immediate flush
            return StreamingResponse(text_stream(), media_type="text/plain")
        else:
            # Non-streaming response
            response = await call_llm(messages, max_tokens, model)
            # If response is a generator, join it
            if hasattr(response, "__iter__") and not isinstance(response, str):
                response = "".join(response)
            elif isinstance(response, dict):
                response = str(response)
            return {"response": response, "model": model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_model_options():
    options = {
        "groq": [
            {"id": model_id, "label": model_id.replace("-", " ").capitalize()}
            for model_id in GROQ_MODELS.keys()
        ],
        "gemini": [
            {"id": model_id, "label": model_id.replace("-", " ").capitalize()}
            for model_id in GEMINI_MODELS.keys()
        ],
        "deepseek": [
            {"id": model_id, "label": model_id.replace("-", " ").capitalize()}
            for model_id in DEEPSEEK_MODELS.keys()
        ]
    }
    return options