from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from pydantic import BaseModel
import os
from typing import Optional, List, Dict
import logging
from dotenv import load_dotenv
from app.llm_service.router import stream_llm_response
from app.llm_service.groq import MODEL_PROVIDERS as GROQ_MODELS
from app.llm_service.gemini import MODEL_PROVIDERS as GEMINI_MODELS
from app.llm_service.deepseek import MODEL_PROVIDERS as DEEPSEEK_MODELS
import json


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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    max_tokens: Optional[int] = 800

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Chat endpoint
@app.post("/chat")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint.
    """
    async def event_generator():
        try:
            messages = [msg.dict() for msg in request.messages]
            async for chunk in stream_llm_response(
                model=request.model,
                messages=messages,
                max_tokens=request.max_tokens
            ):
                # Send as JSON lines for frontend parsing
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Root endpoint
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


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

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
    
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    model_options = get_model_options()
    selected_model = next(iter(GROQ_MODELS.keys()), "")
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "model_options": model_options,
            "selected_model": selected_model
        }
    )