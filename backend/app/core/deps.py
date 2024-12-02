from dataclasses import dataclass
from app.config.credentials import CredentialsInfo
from backend.app.core.cache_manager import CacheManager
from backend.app.core.sync_manager import PandasGBQSync
from backend.app.core.query_processor import QueryProcessor
from app.config.settings import get_settings

@dataclass
class AppDependencies:
    credentials: CredentialsInfo
    sync_manager: PandasGBQSync
    cache_manager: CacheManager
    query_processor: QueryProcessor

def init_dependencies() -> AppDependencies:
    settings = get_settings()
    credentials = CredentialsInfo().init_credentials()
    
    sync_manager = PandasGBQSync(
        creds=credentials,
        database_url=settings.database_url
    )
    
    cache_manager = CacheManager(
        redis_url=settings.redis_url
    )
    
    query_processor = QueryProcessor(
        creds=credentials
    )
    
    return AppDependencies(
        credentials=credentials,
        sync_manager=sync_manager,
        cache_manager=cache_manager,
        query_processor=query_processor
    )