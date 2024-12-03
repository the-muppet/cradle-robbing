from fastapi import FastAPI
from dotenv import load_dotenv
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers
from app.api import router

load_dotenv()

def create_app() -> FastAPI:
    """
    Application factory
    """
    app = FastAPI(title="Cradle-Robbin")

    setup_middleware(app)
    setup_exception_handlers(app)
    app.include_router(router)
    
    return app

app = create_app()