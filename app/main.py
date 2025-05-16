from fastapi import FastAPI, HTTPException, Depends, Request, Response, Depends, Form, Cookie, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Body
from urllib.parse import quote
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv
from app.llm_service.router import call_llm
from app.llm_service.groq import MODEL_PROVIDERS as GROQ_MODELS
from app.llm_service.gemini import MODEL_PROVIDERS as GEMINI_MODELS
from app.llm_service.deepseek import MODEL_PROVIDERS as DEEPSEEK_MODELS
import httpx
import os
import logging
import secrets
import time
import json
import asyncio


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Chatbot API",
    description="FastAPI application for a chatbot with multiple LLM integrations",
    version="0.1.0",
)

sessions = {}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define credentials 
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
if not ADMIN_USERNAME:
    raise ValueError("ADMIN_USERNAME environment variable not set")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable not set")

# Define data models
class Message(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    response: str
    model: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = list(GROQ_MODELS.keys())[0]
    max_tokens: Optional[int] = 12800
    stream: Optional[bool] = False

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Router
router = APIRouter()

# Root endpoint
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def get_session(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        session = sessions[session_id]
        if time.time() - session["created_at"] <= 3600:
            return session
    return None

def require_auth(request: Request):
    session = get_session(request)
    if not session:
        # Redirect to root with notification
        redirect_url = "/?error=You%20need%20to%20login%20to%20access%20this%20page"
        raise RedirectResponse(url=redirect_url, status_code=303)
    return session

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    is_authenticated = False
    username = None
    session = get_session(request)
    if session:
        is_authenticated = True
        username = session["username"]
    error = request.query_params.get("error")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "is_authenticated": is_authenticated,
        "username": username,
        "error": error
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, redirect: str = "/"):
    session = get_session(request)
    if session:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "redirect": redirect})

@app.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    redirect: str = Form("/")
):
    # Validate credentials
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Create session
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = {
            "username": username,
            "created_at": time.time()
        }
        
        # Set cookie - Fix: Remove secure=True for development environments
        response = RedirectResponse(url=redirect, status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=3600,  # 1 hour
            # secure=True,  # Comment out for non-HTTPS environments
            samesite="lax"
        )
        return response
    
    # Invalid credentials
    return RedirectResponse(
        url=f"/login?error=Invalid%20credentials&redirect={quote(redirect)}",
        status_code=303
    )

@app.get("/logout")
async def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    # Remove session
    if session_id and session_id in sessions:
        sessions.pop(session_id)
    
    # Clear cookie
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="session_id")
    return response

# --- Protected endpoints below ---

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    session = get_session(request)
    if not session:
        # Use query parameter to specify the page that required login
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
            "username": session["username"]
        }
    )

@app.post("/chat")
async def chat(request: Request, body: dict = Body(...)):
    session = get_session(request)
    if not session:
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

@app.get("/validate")
async def validate_session(session_id: Optional[str] = Cookie(None)):
    # Check if session exists
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if session is expired (1 hour)
    session = sessions[session_id]
    if time.time() - session["created_at"] > 3600:
        sessions.pop(session_id)
        raise HTTPException(status_code=401, detail="Session expired")
    
    return {"authenticated": True, "username": session["username"]}

async def redirect_if_not_authenticated(request: Request, session_id: Optional[str] = Cookie(None)):
    # Check if session exists
    if not session_id or session_id not in sessions:
        # Get current path to redirect back after login
        current_path = request.url.path
        if request.url.query:
            current_path = f"{current_path}?{request.url.query}"
        
        # Redirect to login with the current URL as redirect parameter
        return RedirectResponse(
            url=f"/login?redirect={quote(current_path)}",
            status_code=303
        )
    
    # Check if session is expired (1 hour)
    session = sessions[session_id]
    if time.time() - session["created_at"] > 3600:
        sessions.pop(session_id)
        return RedirectResponse(
            url=f"/login?redirect={quote(request.url.path)}",
            status_code=303
        )
    
    # Session is valid, return the session data
    return session

