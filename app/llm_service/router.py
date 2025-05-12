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

DEFAULT_MODEL = "gemini-2.5-flash-preview-04-17"

async def call_llm(messages: list, max_tokens: int, model: str):
    """
    Calls the LLM with the given messages and model.
    Returns: LLM response (str or generator)
    """
    if not model:
        model = DEFAULT_MODEL
    for model_dict, handler in PROVIDERS:
        if model in model_dict:
            return await run_in_threadpool(handler, messages, max_tokens, model, True)
    raise ValueError(f"Model '{model}' is not supported.")
