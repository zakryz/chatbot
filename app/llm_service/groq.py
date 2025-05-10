import os
from groq import Groq

MODEL_PROVIDERS = {
    "llama-3.3-70b-versatile": "groq",
    "llama-3.1-8b-instant": "groq",
    "gemma2-9b-it": "groq",
    "meta-llama/llama-4-maverick-17b-128e-instruct": "groq",
    # Add more models/providers as needed
}

def call_groq(messages, max_tokens, model_id, stream=False):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    kwargs = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens if max_tokens is not None else 1024,
        "temperature": 0.5,
        "stream": True
    }
    if stream:
        def generator():
            for chunk in client.chat.completions.create(**kwargs):
                if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        return generator()
    else:
        chat_completion = client.chat.completions.create(**kwargs)
        response_text = ""
        for chunk in chat_completion:
            if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
        return {"response": response_text, "model": model_id}