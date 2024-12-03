import json
import os
import pickle
from redis import Redis
from functools import wraps
import pandas as pd
import numpy as np
from urllib.parse import urlparse
from pydantic import BaseModel

class CacheManager:
    def __init__(self, redis_url=None, expire_time=300):
        if redis_url is None:
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6388')
        
        parsed_url = urlparse(redis_url)
        
        self.redis_client = Redis(
            host=parsed_url.hostname or 'redis',
            port=parsed_url.port or 6388,
            decode_responses=False,
            encoding='utf-8'
        )
        self.expire_time = expire_time

    @staticmethod
    def _serialize_dataframe(df):
        """Serialize DataFrame to a JSON-compatible format"""
        if isinstance(df, pd.DataFrame):
            return {
                'data': df.replace({np.nan: None}).to_dict('records'),
                '_type': 'dataframe',
                'columns': list(df.columns),
                'index': list(df.index)
            }
        return df

    @staticmethod
    def _deserialize_dataframe(data):
        """Deserialize data back to DataFrame if it was a DataFrame"""
        if isinstance(data, dict) and data.get('_type') == 'dataframe':
            return pd.DataFrame(
                data['data'],
                columns=data['columns'],
                index=data['index']
            )
        return data

    def create_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> bytes:
        """Create a deterministic cache key while handling complex objects"""
        def sanitize_value(value):
            if isinstance(value, BaseModel):
                return json.dumps(value.model_dump(), sort_keys=True)
            elif isinstance(value, pd.DataFrame):
                return hash(str(value.shape) + str(list(value.columns)))
            elif isinstance(value, (dict, list, set)):
                return json.dumps(str(value), sort_keys=True)
            return str(value)
            
        processed_args = [sanitize_value(arg) for arg in args]
        processed_kwargs = {k: sanitize_value(v) for k, v in sorted(kwargs.items())}
        
        key_parts = [
            func_name,
            ','.join(map(str, processed_args)),
            ','.join(f"{k}={v}" for k, v in processed_kwargs.items())
        ]
        
        return ':'.join(key_parts).encode('utf-8')

    def cache_response(self, expire_time=None):
        if expire_time is None:
            expire_time = self.expire_time

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    cache_key = self.create_cache_key(func.__name__, args, kwargs)
                    
                    cached_result = await self.redis_client.get(cache_key)
                    if cached_result:
                        try:
                            result = pickle.loads(cached_result)
                            # Ensure we're returning the same type as the original function
                            return self._deserialize_dataframe(result)
                        except Exception as e:
                            print(f"Cache deserialization error: {str(e)}")
                            await self.redis_client.delete(cache_key)
                    
                    # Get fresh result from the original function
                    result = await func(*args, **kwargs)
                    
                    try:
                        serialized_result = self._serialize_dataframe(result)
                        pickled_result = pickle.dumps(serialized_result)
                        await self.redis_client.setex(cache_key, expire_time, pickled_result)
                    except Exception as e:
                        print(f"Cache serialization error: {str(e)}")
                    
                    return result
                except Exception as e:
                    print(f"Cache wrapper error: {str(e)}")
                    return await func(*args, **kwargs)
            
            # Preserve the original function's return type annotation
            wrapper.__annotations__ = func.__annotations__
            return wrapper
        return decorator