from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.config.settings import get_settings

def setup_middleware(app: FastAPI) -> None:
    """
    Configure application middleware with comprehensive CORS settings
    and additional performance optimizations.
    """
    settings = get_settings()
    
    # Configure CORS with explicit settings
    app.add_middleware(
        CORSMiddleware,
        # Allow specific origins or use ["*"] for development
        allow_origins=["http://localhost:5173", "http://172.20.0.6:5173"],
        # Important: these need to be explicitly set
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        allow_credentials=True,
        expose_headers=["*"],
        max_age=3600,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    print("CORS configuration:")
    print(f"- Origins: {settings.cors_origins}")
    print("- Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH")
    print("- Credentials allowed: True")
    print("- Headers allowed: All")