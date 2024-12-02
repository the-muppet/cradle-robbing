# app/api/bigquery/router.py
from typing import List
from fastapi import APIRouter, Depends

from app.core.deps import AppDependencies
from app.core.exceptions import AppException
from app.database.models import QueryResponse, QueryRequest, SyncResponse, SyncTableRequest, SyncDatasetRequest

router = APIRouter(prefix="/api", tags=["bigquery"])

def get_deps(deps: AppDependencies = Depends()) -> tuple:
    """Helper function to extract required dependencies"""
    return deps.query_processor, deps.cache_manager

@router.get("/health")
async def health_check(deps: AppDependencies = Depends()):
    processor = deps.query_processor
    try:
        await processor.execute_gbq_query("SELECT 1")
        bigquery_status = "healthy"
    except Exception as e:
        bigquery_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "bigquery": bigquery_status
    }

@router.get("/")
async def root():
    routes = [{"path": route.path, "name": route.name} for route in router.routes]
    return {
        "message": """Welcome to Elmos Hacktaskic BigQuery Exploration API!
        Fun fact: Service account credentials dont give one access to the BigQuery Interface so.. here we are. lol.""",
        "routes": routes
    }

@router.get("/datasets")
async def get_datasets(deps: AppDependencies = Depends()) -> List[str]:
    processor, cache_manager = get_deps(deps)
    
    @cache_manager.cache_response(expire_time=300)
    async def _get_datasets():
        query = """
        SELECT schema_name
        FROM INFORMATION_SCHEMA.SCHEMATA
        WHERE schema_name NOT IN ('INFORMATION_SCHEMA', 'pg_catalog')
        ORDER BY schema_name
        """
        df = await processor.execute_gbq_query(query)
        return df['schema_name'].tolist()
    
    return await _get_datasets()

@router.get("/datasets/{dataset_id}/tables")
async def get_tables(
    dataset_id: str, 
    deps: AppDependencies = Depends()
) -> List[str]:
    processor = deps.query_processor
    try:
        query = f"""
        SELECT table_name
        FROM {dataset_id}.INFORMATION_SCHEMA.TABLES
        WHERE table_schema = '{dataset_id}'
        ORDER BY table_name
        """
        df = await processor.execute_gbq_query(query)
        return df['table_name'].tolist()
    except Exception as e:
        raise AppException(f"Error fetching tables: {str(e)}")

@router.get("/datasets/{dataset_id}/tables/{table_id}")
async def get_table_info(
    dataset_id: str, 
    table_id: str, 
    result_limit: int = 5,
    deps: AppDependencies = Depends()
):
    processor = deps.query_processor
    try:
        schema_query = f"""
        SELECT column_name as name, data_type as type
        FROM {dataset_id}.INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = '{table_id}'
        ORDER BY ordinal_position
        """
        schema_df = await processor.execute_gbq_query(schema_query)
        schema = processor.serialize_dataframe(schema_df)
        
        preview_query = f"SELECT * FROM `{dataset_id}.{table_id}` LIMIT {result_limit}"
        preview_df = await processor.execute_gbq_query(preview_query)
        preview = processor.serialize_dataframe(preview_df)
        
        count_query = f"SELECT COUNT(*) as count FROM `{dataset_id}.{table_id}`"
        count_df = await processor.execute_gbq_query(count_query)
        row_count = int(count_df['count'].iloc[0])
        
        return {
            "row_count": row_count,
            "schema": schema,
            "preview": preview
        }
    except Exception as e:
        raise AppException(f"Error fetching table info: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def execute_query(
    query_request: QueryRequest, 
    deps: AppDependencies = Depends()
):
    processor = deps.query_processor
    try:
        if not query_request.query.lower().strip().startswith('select'):
            raise AppException("Only SELECT queries are allowed", status_code=400)
        
        df = await processor.execute_gbq_query(query_request.query)
        
        return {
            "rows": processor.serialize_dataframe(df),
            "schema": [
                {
                    "name": str(col),
                    "type": str(df[col].dtype).upper()
                } for col in df.columns
            ],
            "total_rows": len(df)
        }
    except Exception as e:
        raise AppException(f"Query execution error: {str(e)}")

@router.get("/datasets/{dataset_id}/stats")
async def get_dataset_stats(
    dataset_id: str, 
    deps: AppDependencies = Depends()
):
    processor, cache_manager = get_deps(deps)
    
    @cache_manager.cache_response(expire_time=300)
    async def _get_stats():
        stats_query = f"""
        SELECT 
            COUNT(*) as table_count,
            SUM(size_bytes) as total_size_bytes,
            MAX(last_modified_time) as last_modified,
            MIN(creation_time) as created
        FROM {dataset_id}.__TABLES__
        """
        stats_df = await processor.execute_gbq_query(stats_query)
        stats = stats_df.iloc[0].to_dict()
        
        return {
            "table_count": int(stats['table_count']),
            "total_size_bytes": int(stats['total_size_bytes']),
            "last_modified": stats['last_modified'],
            "created": stats['created'],
            "description": None,
            "labels": {}
        }
    
    return await _get_stats()


@router.post("/sync/table", response_model=SyncResponse)
async def sync_table(
    request: SyncTableRequest,
    deps: AppDependencies = Depends()
):
    """
    Sync a single table from BigQuery to PostgreSQL
    
    Args:
        request: SyncTableRequest containing dataset_id, table_id and optional chunksize
        deps: Application dependencies
    
    Returns:
        SyncResponse with status and details of the sync operation
    """
    try:
        result = await deps.sync_manager.sync_table(
            request.dataset_id,
            request.table_id,
            request.chunksize
        )
        
        if result["status"] == "error":
            raise AppException(result["message"])
            
        return result
    except Exception as e:
        raise AppException(f"Table sync failed: {str(e)}")

@router.post("/sync/dataset", response_model=SyncResponse)
async def sync_dataset(
    request: SyncDatasetRequest,
    deps: AppDependencies = Depends()
):
    """
    Sync all tables in a dataset from BigQuery to PostgreSQL
    
    Args:
        request: SyncDatasetRequest containing dataset_id and optional exclude_tables list
        deps: Application dependencies
    
    Returns:
        SyncResponse with status and details of the sync operation
    """
    try:
        result = await deps.sync_manager.sync_dataset(
            request.dataset_id,
            request.exclude_tables
        )
        
        if result["status"] == "error":
            raise AppException(result["message"])
            
        return result
    except Exception as e:
        raise AppException(f"Dataset sync failed: {str(e)}")

@router.get("/sync/status")
async def get_sync_status(deps: AppDependencies = Depends()):
    """
    Get sync status for all tables
    
    Args:
        deps: Application dependencies
    
    Returns:
        Dictionary containing sync status for all tables
    """
    try:
        return await deps.sync_manager.get_sync_status()
    except Exception as e:
        raise AppException(f"Failed to get sync status: {str(e)}")

@router.get("/sync/analyze/{dataset_id}/{table_id}", response_model=SyncResponse)
async def analyze_table(
    dataset_id: str,
    table_id: str,
    deps: AppDependencies = Depends()
):
    """
    Get detailed analysis of a synced table
    
    Args:
        dataset_id: ID of the dataset containing the table
        table_id: ID of the table to analyze
        deps: Application dependencies
    
    Returns:
        SyncResponse with analysis details
    """
    try:
        result = await deps.sync_manager.analyze_table(dataset_id, table_id)
        
        if "status" in result and result["status"] == "error":
            raise AppException(result["message"])
            
        return result
    except Exception as e:
        raise AppException(f"Table analysis failed: {str(e)}")