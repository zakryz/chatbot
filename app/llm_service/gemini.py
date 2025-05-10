import os
from google import genai
from google.genai import types

MODEL_PROVIDERS = {
    "gemini-2.5-flash-preview-04-17": "gemini",
    "gemini-2.5-pro-exp-03-25": "gemini"
    # Add more models/providers as needed
}

def call_gemini(messages, max_tokens, model_id, stream=False):
    if isinstance(messages, list):
        user_text = "\n".join([m.get("content", "") for m in messages])
    else:
        user_text = str(messages)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_text)],
        ),
    ]

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        max_output_tokens=max_tokens if max_tokens else None
    )

    if stream:
        def generator():
            for chunk in client.models.generate_content_stream(
                model=model_id,
                contents=contents,
                config=generate_content_config,
            ):
                text = getattr(chunk, "text", "") or ""
                if text:
                    yield text
        return generator()
    else:
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model_id,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += getattr(chunk, "text", "") or ""
        return {"response": response_text, "model": model_id}