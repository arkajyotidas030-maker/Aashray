"""Isolated API for Playwright. Not used in the jury demo."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
(ROOT / "e2e_playwright.db").unlink(missing_ok=True)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("aashray.main:app", host="127.0.0.1", port=8010, reload=False)
