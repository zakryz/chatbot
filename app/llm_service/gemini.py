import os
from google import genai
from google.genai import types

MODEL_PROVIDERS = {
    "gemini-2.5-flash-preview-04-17": "gemini",
    "gemini-2.5-pro-exp-03-25": "gemini"
    # Add more models/providers as needed
}

def call_gemini(messages, max_tokens, model_id, stream=False):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")

    if isinstance(messages, list) and messages and isinstance(messages[0], dict):
        messages = [m["content"] for m in messages]

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_id,
        contents=messages,
        config=types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=max_tokens if max_tokens is not None else 8192
        ),
    )
    if not stream:
        return response.text

    def _stream_generator():
        response = client.models.generate_content_stream(
            model=model_id,
            contents=messages,
            config=types.GenerateContentConfig(
                temperature=0.5,
                max_output_tokens=max_tokens if max_tokens is not None else 8192
            ),
        )
        for chunk in response:
            if hasattr(chunk, "text") and chunk.text:
                yield chunk.text
                
    return _stream_generator()
