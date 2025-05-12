import os
from openai import OpenAI
from typing import Generator, Union

MODEL_PROVIDERS = {
    "deepseek-chat": "deepseek",
    "deepseek-reasoner": "deepseek"
}

def call_deepseek(messages, max_tokens, model_id, stream=True) -> Union[str, Generator[str, None, None]]:
    client = OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
    kwargs = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens if max_tokens is not None else 8192,
        "temperature": 0.7,
        "stream": stream
    }
    if not stream:
        return client.chat.completions.create(**kwargs).choices[0].message.content

    def _stream_generator():
        response = client.chat.completions.create(**kwargs)
        for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield delta.content
    return _stream_generator()