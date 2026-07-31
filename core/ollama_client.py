"""
Thin wrapper around the local Ollama HTTP API.

Requires Ollama running locally (https://ollama.com) with two models pulled:
  ollama pull llama3.1        # generation / extraction
  ollama pull nomic-embed-text  # embeddings

No API key, no cloud calls — everything runs on localhost:11434.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error

OLLAMA_HOST = "http://localhost:11434"


class OllamaError(RuntimeError):
    pass


def _post(path: str, payload: dict) -> dict:
    url = f"{OLLAMA_HOST}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        raise OllamaError(
            f"Could not reach Ollama at {url}. Is it running? Start it with `ollama serve`, "
            f"and make sure you've pulled the model. Original error: {e}"
        ) from e


def chat(prompt: str, system: str = "", model: str = "llama3.1", json_mode: bool = False) -> str:
    """Single-turn chat completion. Returns the assistant's text."""
    payload = {
        "model": model,
        "messages": ([{"role": "system", "content": system}] if system else [])
        + [{"role": "user", "content": prompt}],
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"
    result = _post("/api/chat", payload)
    return result["message"]["content"]


def embed(text: str, model: str = "nomic-embed-text") -> list[float]:
    """Returns an embedding vector for a piece of text."""
    result = _post("/api/embeddings", {"model": model, "prompt": text})
    return result["embedding"]


def embed_batch(texts: list[str], model: str = "nomic-embed-text") -> list[list[float]]:
    return [embed(t, model=model) for t in texts]
