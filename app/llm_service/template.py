import os
import httpx
from groq import Groq

GROQ_MODELS = {
    "llama-3.3-70b-versatile": {
        "context_window": 128000,
        "max_tokens": 32768,
    },
    "llama-3.1-8b-instant": {
        "context_window": 128000,
        "max_tokens": 8192,
    },
    "gemma2-9b-it": {
        "context_window": 8192,
        "max_tokens": None,
    },
    "meta-llama/llama-4-maverick-17b-128e-instruct": {
        "context_window": 128000,
        "max_tokens": 8192,
    },
    # Add more models as needed
}

async def get_llm_response(model: str, messages: list, max_tokens: int):
    """
    Get a response from the specified LLM model via Groq.
    Args:
        model (str): Model ID (must match a key in GROQ_MODELS)
        messages (list): List of message dicts [{role, content}]
        max_tokens (int): Max tokens for completion
    Returns:
        dict: {"response": str, "model": str}
    """
    if model not in GROQ_MODELS:
        raise ValueError(f"Model '{model}' is not supported.")
    return await call_groq(messages, max_tokens, model)

async def call_groq(messages, max_tokens, model_id):
    """
    Call the Groq API with the specified model and messages.
    Args:
        messages (list): List of message dicts
        max_tokens (int): Max tokens for completion
        model_id (str): Model ID
    Returns:
        dict: {"response": str, "model": str}
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    if not isinstance(messages, list) or not all(isinstance(m, dict) for m in messages):
        raise ValueError("messages must be a list of dicts with 'role' and 'content'.")
    kwargs = {"model": model_id, "messages": messages}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    chat_completion = client.chat.completions.create(**kwargs)
    response_text = chat_completion.choices[0].message.content if chat_completion.choices else ""
    return {"response": response_text, "model": model_id}
