import os
from openai import OpenAI

MODEL_PROVIDERS = {
    "deepseek-chat": "deepseek",
    "deepseek-reasoner": "deepseek"
}

def call_deepseek(messages, max_tokens, model_id, stream=False):
    client = OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
    kwargs = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens if max_tokens is not None else 1024,
        "temperature": 0.7,
        "stream": True
    }
    if stream:
        def generator():
            for chunk in client.chat.completions.create(**kwargs):
                if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        return generator()
    else:
        response_text = ""
        for chunk in client.chat.completions.create(**kwargs):
            if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
        return {"response": response_text, "model": model_id}