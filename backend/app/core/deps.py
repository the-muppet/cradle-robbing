from functools import lru_cache
from app.config.credentials import CredentialsInfo
from app.core.cache_manager import CacheManager
from app.core.sync_manager import PandasGBQSync
from app.core.query_processor import QueryProcessor
from app.config.settings import get_settings

@lru_cache()
def get_app_dependencies():
    """
    Creates and caches application dependencies.
    Using lru_cache ensures we only create these objects once.
    """
    settings = get_settings()
    credentials = CredentialsInfo().init_credentials()
    
    return {
        'sync_manager': PandasGBQSync(
            creds=credentials,
            database_url=settings.database_url
        ),
        'cache_manager': CacheManager(
            redis_url=settings.redis_url
        ),
        'query_processor': QueryProcessor(
            creds=credentials
        )
    }

async def get_processor():
    """Dependency that provides the QueryProcessor"""
    return get_app_dependencies()['query_processor']

async def get_cache_manager():
    """Dependency that provides the CacheManager"""
    return get_app_dependencies()['cache_manager']

async def get_sync_manager():
    """Dependency that provides the PandasGBQSync"""
    return get_app_dependencies()['sync_manager']