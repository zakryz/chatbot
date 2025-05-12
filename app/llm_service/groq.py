import os
from openai import OpenAI
from typing import Generator, Union

MODEL_PROVIDERS = {
    "llama-3.3-70b-versatile": "groq",
    "llama-3.1-8b-instant": "groq",
    "gemma2-9b-it": "groq",
    "meta-llama/llama-4-maverick-17b-128e-instruct": "groq",
    # Add more models/providers as needed
}

def call_groq(
    messages: list,
    max_tokens: int,
    model_id: str,
    stream: bool = False
) -> Union[str, Generator[str, None, None]]:
    """
    Call the Groq-backed OpenAI API for chat completions.
    Supports streaming according to OpenAI API docs.
    """
    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )
    kwargs = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens or 8192,
        "temperature": 0.5,
        "stream": stream
    }
    if not stream:
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def _stream_generator():
        response = client.chat.completions.create(**kwargs)
        for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield delta.content
    return _stream_generator()
