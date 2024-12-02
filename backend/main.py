from fastapi import FastAPI
from app import create_app

def get_application() -> FastAPI:
    return create_app()

__all__ = [
    "get_application",
    "create_app",
]