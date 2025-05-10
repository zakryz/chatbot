from .groq import call_groq, MODEL_PROVIDERS as GROQ_MODELS
from .gemini import call_gemini, MODEL_PROVIDERS as GEMINI_MODELS
from .deepseek import call_deepseek, MODEL_PROVIDERS as DEEPSEEK_MODELS

PROVIDERS = [
    (GROQ_MODELS, call_groq),
    (GEMINI_MODELS, call_gemini),
    (DEEPSEEK_MODELS, call_deepseek)
    # Add more providers here as (MODEL_DICT, HANDLER)
]

async def get_llm_response(model: str, messages: list, max_tokens: int):
    for model_dict, handler in PROVIDERS:
        if model in model_dict:
            return await handler(messages, max_tokens, model)
    raise ValueError(f"Model '{model}' is not supported.")