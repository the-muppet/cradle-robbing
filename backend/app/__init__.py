from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from backend.app.core.deps import init_dependencies, AppDependencies
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers
from app.api import router

load_dotenv()

def create_app() -> FastAPI:
    """
    Application factory
    """
    app = FastAPI(title="Cradle-Robbin")
    deps = init_dependencies()
    
    async def get_dependencies() -> AppDependencies:
        return deps

    setup_middleware(app)
    setup_exception_handlers(app)
    
    app.include_router(router, dependencies=[Depends(get_dependencies)])
    
    return app