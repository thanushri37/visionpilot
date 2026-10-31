"""VisionPilot's one doorway to the Meta model.

Every part of VisionPilot that needs the model (planner, verifier,
final check) calls ask(). Settings come from .env, never from code.
"""
import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _setting(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is missing from .env")
    return value


MODEL = _setting("MODEL_API_MODEL")
_client = OpenAI(
    base_url=_setting("MODEL_API_BASE_URL"),  # Meta's address, not OpenAI's
    api_key=_setting("MODEL_API_KEY"),
    timeout=90,       # seconds to wait before giving up on one call
    max_retries=3,    # retry automatically when Meta is busy
)

_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def _image_part(path):
    """Turn a screenshot file into base64 text the API can carry."""
    p = Path(path)
    mime = _MIME.get(p.suffix.lower(), "image/png")
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def ask(prompt, images=(), system=None):
    """Send text plus optional screenshots to the model; return its reply text."""
    content = [{"type": "text", "text": prompt}] + [_image_part(p) for p in images]
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": content})
    response = _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,  # same screen, same answer: makes testing reliable
    )
    return response.choices[0].message.content
