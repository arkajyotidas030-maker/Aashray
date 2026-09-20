"""Thin optional LLM client. Never writes geometry, ranks, or blocked edges."""

from __future__ import annotations

import json

import httpx

from aashray.config import get_settings

TIMEOUT = 4.0


def classify_text(raw_text: str) -> dict | None:
    settings = get_settings()
    if not settings.llm_api_key or not settings.llm_base_url:
        return None
    prompt = (
        "Extract emergency_type (landslide|blocked_road|trapped|other), "
        "severity 0-5, people_count integer from this citizen text. "
        "JSON only, no geometry.\n"
        f"TEXT: {raw_text[:500]}"
    )
    data = _complete(prompt)
    if not data:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def draft_sitrep(payload: dict) -> str | None:
    settings = get_settings()
    if not settings.llm_api_key or not settings.llm_base_url:
        return None
    prompt = (
        "Write a 20-word responder sitrep from this JSON. "
        "Do not invent coordinates, roads, or missing persons.\n"
        + json.dumps(payload)[:2000]
    )
    return _complete(prompt)


def _complete(prompt: str) -> str | None:
    settings = get_settings()
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0,
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            res = client.post(url, headers=headers, json=body)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
