"""Insurance Cross-Sell Predictor backend package.

Re-export the FastAPI ``app`` so ``uvicorn app:app`` keeps working after the
move from a single ``app.py`` module to this package.
"""

from app.main import app

__all__ = ["app"]
