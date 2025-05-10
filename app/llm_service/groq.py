import os
from groq import Groq

MODEL_PROVIDERS = {
    "llama-3.3-70b-versatile": "groq",
    "llama-3.1-8b-instant": "groq",
    "gemma2-9b-it": "groq",
    "meta-llama/llama-4-maverick-17b-128e-instruct": "groq",
    # Add more models/providers as needed
}

async def call_groq(messages, max_tokens, model_id):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    kwargs = {"model": model_id, "messages": messages}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    chat_completion = client.chat.completions.create(**kwargs)
    response_text = chat_completion.choices[0].message.content if chat_completion.choices else ""
    return {"response": response_text, "model": model_id}