import os
import re
import json
import pickle
import asyncio
import numpy as np
import pandas_gbq
from functools import wraps
from pydantic import BaseModel
from redis.asyncio import Redis
from typing import Any, List, Optional
from google.oauth2 import service_account
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from model.models import QueryResponse, QueryRequest

# Initialize credentials and project_id
credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
if not credentials_json:
    raise Exception("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")

credentials_info = json.loads(credentials_json)
project_id = credentials_info.get('project_id')
if not project_id:
    raise Exception("project_id not found in credentials")

# Create credentials object once
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Configure pandas_gbq globally
pandas_gbq.context.credentials = credentials
pandas_gbq.context.project = project_id

# Redis client
redis_client = Redis(
    host=os.getenv('REDIS_URL', 'redis').split('://')[1].split(':')[0],
    port=6388,
    decode_responses=False,
    encoding='utf-8'
)

def create_cache_key(func_name: str, args: tuple, kwargs: dict) -> bytes:
    """Create a deterministic cache key while avoiding circular references"""
    
    def sanitize_value(value):
        if isinstance(value, BaseModel):

            return json.dumps(value.model_dump(), sort_keys=True)
        elif isinstance(value, (dict, list, set)):
            return json.dumps(value, sort_keys=True)
        else:
            return str(value)
        
    processed_args = [sanitize_value(arg) for arg in args]
    processed_kwargs = {k: sanitize_value(v) for k, v in sorted(kwargs.items())}
    
    key_parts = [
        func_name,
        ','.join(processed_args),
        ','.join(f"{k}={v}" for k, v in processed_kwargs.items())
    ]
    
    return ':'.join(key_parts).encode('utf-8')


def cache_response(expire_time=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                cache_key = create_cache_key(func.__name__, args, kwargs)
                
                for retry in range(3):
                    try:
                        cached_result = await redis_client.get(cache_key)
                        if cached_result:
                            try:
                                return pickle.loads(cached_result)
                            except (pickle.UnpicklingError, TypeError, ValueError) as e:
                                await redis_client.delete(cache_key)
                                break
                        break
                    except Exception as e:
                        if retry == 2:
                            print(f"Redis get error after retries: {str(e)}")
                        await asyncio.sleep(0.1 * (retry + 1))
                
                result = await func(*args, **kwargs)
                
                for retry in range(3):
                    try:
                        pickled_result = pickle.dumps(result)
                        await redis_client.setex(cache_key, expire_time, pickled_result)
                        break
                    except Exception as e:
                        if retry == 2:
                            print(f"Redis set error after retries: {str(e)}")
                        await asyncio.sleep(0.1 * (retry + 1)) 
                
                return result
            except Exception as e:
                print(f"Cache wrapper error: {str(e)}")
                # If caching fails, still return the result
                return await func(*args, **kwargs)
        return wrapper
    return decorator

def convert_numpy_types(obj):
    """Convert NumPy types to native Python types"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, np.bool_)):
        return bool(obj)
    elif isinstance(obj, np.datetime64):
        return obj.astype(str)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

def serialize_dataframe(df):
    """Convert a pandas DataFrame to a JSON-serializable format"""
    records = df.replace({np.nan: None}).to_dict('records')
    return json.loads(json.dumps(records, default=convert_numpy_types))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryProcessor:
    def __init__(self, project_id: str):
        self.project_id = project_id
    
    def qualify_table_references(self, query: str) -> str:
        """Add project ID to unqualified table references."""
        # Pattern to match table references like `dataset.table` but not `project.dataset.table`
        pattern = r'`([^`\.]+\.[^`\.]+)`'
        
        def replace_match(match):
            table_ref = match.group(1)
            if '.' in table_ref and not table_ref.startswith(f"{self.project_id}."):
                return f'`{self.project_id}.{table_ref}`'
            return match.group(0)
        
        return re.sub(pattern, replace_match, query)

    def generate_alias(self, table_name: str) -> str:
        """Generate a meaningful alias for a table."""
        parts = table_name.split('.')[-1].split('_')
        alias = ''.join(word[0] for word in parts if len(word) > 2)
        return alias.lower() or 't' 
    
    def build_select_query(
            self, 
            fields: list[str], 
            table_name: str, 
            conditions: Optional[list[str]] = None,
            group_by: Optional[list[str]] = None,
            order_by: Optional[list[str]] = None,
            limit: Optional[int] = None
        ) -> str:
        """Build a SELECT query from components."""
        table_alias = self.generate_alias(table_name)
        qualified_table = f"`{self.project_id}.{table_name}`"
        
        # Add alias to field references
        aliased_fields = [f"{table_alias}.{field}" for field in fields]
        
        query = f"SELECT {', '.join(aliased_fields)}\nFROM {qualified_table} AS {table_alias}"
        
        if conditions:
            query += f"\nWHERE {' AND '.join(conditions)}"
        
        if group_by:
            query += f"\nGROUP BY {', '.join(group_by)}"
            
        if order_by:
            query += f"\nORDER BY {', '.join(order_by)}"
            
        if limit:
            query += f"\nLIMIT {limit}"
        
        return query

async def execute_gbq_query(query: str, project_id: str, credentials: Any):
    """Enhanced query execution with automatic project ID qualification."""
    processor = QueryProcessor(project_id)
    qualified_query = processor.qualify_table_references(query)
    print(f"Original query: {query}")
    print(f"Qualified query: {qualified_query}")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: pandas_gbq.read_gbq(
            qualified_query,
            project_id=project_id,
            credentials=credentials
        )
    )

@app.get("/health")
async def health_check():
    try:
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    try:
        await execute_gbq_query("SELECT 1")
        bigquery_status = "healthy"
    except Exception as e:
        bigquery_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "redis": redis_status,
        "bigquery": bigquery_status
    }

@app.get("/api")
async def root():
    routes = [{"path": route.path, "name": route.name} for route in app.routes]
    return {
        "message": """Welcome to Elmos Hacktaskic BigQuery Exploration API!
        Fun fact: Service account credentials dont give one access to the BigQuery Interface so.. here we are. lol.""",
        "routes": routes
    }

@app.get("/api/datasets")
@cache_response(expire_time=3600)
async def get_datasets() -> List[str]:
    query = """
    SELECT schema_name
    FROM INFORMATION_SCHEMA.SCHEMATA
    WHERE schema_name NOT IN ('INFORMATION_SCHEMA', 'pg_catalog')
    ORDER BY schema_name
    """
    df = await execute_gbq_query(query)
    return df['schema_name'].tolist()

@app.get("/api/datasets/{dataset_id}/tables")
@cache_response(expire_time=1800)
async def get_tables(dataset_id: str) -> List[str]:
    query = f"""
    SELECT table_name
    FROM {dataset_id}.INFORMATION_SCHEMA.TABLES
    WHERE table_schema = '{dataset_id}'
    ORDER BY table_name
    """
    df = await execute_gbq_query(query)
    return df['table_name'].tolist()

@app.get("/api/datasets/{dataset_id}/tables/{table_id}")
@cache_response(expire_time=300)
async def get_table_info(dataset_id: str, table_id: str, result_limit: int = 5):
    try:
        # Get schema
        schema_query = f"""
        SELECT column_name as name, data_type as type
        FROM {dataset_id}.INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = '{table_id}'
        ORDER BY ordinal_position
        """
        schema_df = await execute_gbq_query(schema_query)
        schema = serialize_dataframe(schema_df)
        
        # Get preview
        preview_query = f"SELECT * FROM `{dataset_id}.{table_id}` LIMIT {result_limit}"
        preview_df = await execute_gbq_query(preview_query)
        preview = serialize_dataframe(preview_df)
        
        # Get row count
        count_query = f"SELECT COUNT(*) as count FROM `{dataset_id}.{table_id}`"
        count_df = await execute_gbq_query(count_query)
        row_count = int(count_df['count'].iloc[0])
        
        return JSONResponse(content={
            "row_count": row_count,
            "schema": schema,
            "preview": preview
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query",  response_model=QueryResponse)
@cache_response(expire_time=300)
async def execute_query(query_request: QueryRequest):
    try:
        if not query_request.query.lower().strip().startswith('select'):
            raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
        
        processor = QueryProcessor(project_id)
        qualified_query = processor.qualify_table_references(query_request.query)
        
        df = await execute_gbq_query(qualified_query, project_id, credentials)
        
        return JSONResponse(content={
            "rows": serialize_dataframe(df),
            "schema": [
                {
                    "name": str(col),
                    "type": str(df[col].dtype).upper()
                } for col in df.columns
            ],
            "total_rows": len(df)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/datasets/{dataset_id}/stats")
@cache_response(expire_time=600)
async def get_dataset_stats(dataset_id: str):
    stats_query = f"""
    SELECT 
        COUNT(*) as table_count,
        SUM(size_bytes) as total_size_bytes,
        MAX(last_modified_time) as last_modified,
        MIN(creation_time) as created
    FROM {dataset_id}.__TABLES__
    """
    stats_df = await execute_gbq_query(stats_query)
    stats = stats_df.iloc[0].to_dict()
    
    return {
        "table_count": int(stats['table_count']),
        "total_size_bytes": int(stats['total_size_bytes']),
        "last_modified": stats['last_modified'],
        "created": stats['created'],
        "description": None,
        "labels": {}
    }