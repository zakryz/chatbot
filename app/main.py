from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Body
from pydantic import BaseModel
import os
from typing import Optional, List, Dict
import logging
from dotenv import load_dotenv
from app.llm_service.router import call_llm
from app.llm_service.groq import MODEL_PROVIDERS as GROQ_MODELS
from app.llm_service.gemini import MODEL_PROVIDERS as GEMINI_MODELS
from app.llm_service.deepseek import MODEL_PROVIDERS as DEEPSEEK_MODELS
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
    max_tokens: Optional[int] = 12800
    stream: Optional[bool] = False

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Chat endpoint supporting streaming and non-streaming
@app.post("/chat")
async def chat(request: Request, body: dict = Body(...)):
    """
    Chat endpoint supporting streaming and non-streaming.
    """
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