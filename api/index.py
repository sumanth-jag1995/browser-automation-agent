"""Vercel Python serverless entry point — imports the FastAPI app from main.py."""
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from main import app` resolves
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app  # noqa: F401, E402
