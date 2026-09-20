import json
from functools import lru_cache
from pathlib import Path

PACK_PATH = Path(__file__).resolve().parent.parent / "scenario" / "pack.json"


@lru_cache
def load_pack() -> dict:
    return json.loads(PACK_PATH.read_text(encoding="utf-8"))
