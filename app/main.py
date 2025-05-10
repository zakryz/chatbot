from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from pydantic import BaseModel
import os
from typing import Optional, List, Dict
import logging
from dotenv import load_dotenv
from app.llm_service.router import get_llm_response 


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

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "groq"  # Default model
    max_tokens: Optional[int] = 800

class ChatResponse(BaseModel):
    response: str
    model: str

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Log the incoming request
        logger.info(f"Received chat request for model: {request.model}")
        
        # Convert Pydantic models to dictionaries for our LLM service
        messages = [msg.dict() for msg in request.messages]
        
        # Get response from the specified LLM
        response_data = await get_llm_response(
            model=request.model,
            messages=messages,
            max_tokens=request.max_tokens
        )
        
        # Return the response
        return ChatResponse(
            response=response_data["response"],
            model=response_data["model"]
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat")
async def chat_endpoint():
    return {"message": "Welcome to the Chatbot API. Use /chat endpoint to communicate with the bot."}