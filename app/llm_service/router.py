from fastapi.concurrency import run_in_threadpool
from .groq import call_groq, MODEL_PROVIDERS as GROQ_MODELS
from .gemini import call_gemini, MODEL_PROVIDERS as GEMINI_MODELS
from .deepseek import call_deepseek, MODEL_PROVIDERS as DEEPSEEK_MODELS
import asyncio

PROVIDERS = [
    (GROQ_MODELS, call_groq),
    (GEMINI_MODELS, call_gemini),
    (DEEPSEEK_MODELS, call_deepseek)
    # Add more providers here as (MODEL_DICT, HANDLER)
]

DEFAULT_MODEL = "llama-3.1-8b-instant"

async def stream_llm_response(model: str, messages: list, max_tokens: int):
    """
    Async generator for streaming LLM responses.
    Yields: text chunks (str)
    """
    if not model:
        model = DEFAULT_MODEL
    for model_dict, handler in PROVIDERS:
        if model in model_dict:
            # Handler must be a streaming generator
            gen = handler(messages, max_tokens, model, stream=True)
            if asyncio.iscoroutinefunction(gen):
                async for chunk in gen:
                    yield chunk
            else:
                for chunk in gen:
                    yield chunk
            return
    raise ValueError(f"Model '{model}' is not supported.")