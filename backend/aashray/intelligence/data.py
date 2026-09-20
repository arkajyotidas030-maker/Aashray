from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

SCENARIO = Path(__file__).resolve().parent.parent / "scenario"


@lru_cache
def load_json(name: str) -> dict:
    return json.loads((SCENARIO / name).read_text(encoding="utf-8"))


def load_graph() -> dict:
    return load_json("graph.json")


def load_fc(name: str) -> dict:
    return load_json(name)
