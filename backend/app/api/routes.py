from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.core.deps import get_cache_manager, get_processor, get_sync_manager
from app.core.exceptions import AppException
from app.database.models import (
    QueryRequest,
    SyncTableRequest,
    SyncDatasetRequest,
    DatasetStats
)
from app.core.cache_manager import CacheManager
from app.core.query_processor import QueryProcessor
from app.core.sync_manager import PandasGBQSync
from app.database.postgres_con import get_db_session

router = APIRouter(prefix="/api", tags=["bigquery"])


@router.get("/", response_class=JSONResponse)
async def root():
    """Provides API welcome message and available routes."""
    routes = [{"path": route.path, "name": route.name} for route in router.routes]
    return {
        "message": """Welcome to Elmos Hacktaskic BigQuery Exploration API!
        Fun fact: Service account credentials dont give one access to the BigQuery Interface so.. here we are. lol.""",
        "routes": routes,
    }


@router.get("/datasets", response_model=List[str])
async def get_datasets(
    processor: QueryProcessor = Depends(get_processor),
    cache: CacheManager = Depends(get_cache_manager),
):
    """Get list of available datasets."""

    @cache.cache_response(expire_time=300)
    async def _get_datasets() -> List[str]:
        query = """
        SELECT schema_name
        FROM INFORMATION_SCHEMA.SCHEMATA
        WHERE schema_name NOT IN ('INFORMATION_SCHEMA', 'pg_catalog')
        ORDER BY schema_name
        """
        df = await processor.execute_gbq_query(query)
        return df["schema_name"].tolist()

    return await _get_datasets()


@router.get("/datasets/{dataset_id}/tables", response_model=List[str])
async def get_tables(
    dataset_id: str, processor: QueryProcessor = Depends(get_processor)
):
    """Get list of tables in a dataset."""
    try:
        query = f"""
        SELECT table_name
        FROM {dataset_id}.INFORMATION_SCHEMA.TABLES
        WHERE table_schema = '{dataset_id}'
        ORDER BY table_name
        """
        df = await processor.execute_gbq_query(query)
        return df["table_name"].tolist()
    except Exception as e:
        raise AppException(f"Error fetching tables: {str(e)}")


@router.get("/datasets/{dataset_id}/tables/{table_id}")
async def get_table_info(
    dataset_id: str,
    table_id: str,
    result_limit: int = 5,
    processor: QueryProcessor = Depends(get_processor),
):
    """Get detailed information about a specific table."""
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
        row_count = int(count_df["count"].iloc[0])

        return {"row_count": row_count, "schema": schema, "preview": preview}
    except Exception as e:
        raise AppException(f"Error fetching table info: {str(e)}")


@router.post("/query")
async def execute_query(
    query_request: QueryRequest, processor: QueryProcessor = Depends(get_processor)
):
    """Execute a custom query on BigQuery."""
    try:
        if not query_request.query.lower().strip().startswith("select"):
            raise AppException("Only SELECT queries are allowed", status_code=400)

        df = await processor.execute_gbq_query(query_request.query)

        return {
            "rows": processor.serialize_dataframe(df),
            "schema": [
                {"name": str(col), "type": str(df[col].dtype).upper()}
                for col in df.columns
            ],
            "total_rows": len(df),
        }
    except Exception as e:
        raise AppException(f"Query execution error: {str(e)}")


@router.post("/sync/table")
async def sync_table(
    request: SyncTableRequest, sync_manager: PandasGBQSync = Depends(get_sync_manager)
):
    """Sync a single table from BigQuery to PostgreSQL."""
    try:
        result = await sync_manager.sync_table(
            request.dataset_id, request.table_id, request.chunksize
        )
        if result["status"] == "error":
            raise AppException(result["message"])
        return result
    except Exception as e:
        raise AppException(f"Table sync failed: {str(e)}")


@router.post("/sync/dataset")
async def sync_dataset(
    request: SyncDatasetRequest, sync_manager: PandasGBQSync = Depends(get_sync_manager)
):
    """Sync an entire dataset from BigQuery to PostgreSQL."""
    try:
        result = await sync_manager.sync_dataset(
            request.dataset_id, request.exclude_tables
        )
        if result["status"] == "error":
            raise AppException(result["message"])
        return result
    except Exception as e:
        raise AppException(f"Dataset sync failed: {str(e)}")


@router.get("/sync/status")
async def get_sync_status(sync_manager: PandasGBQSync = Depends(get_sync_manager)):
    """Get the current sync status of all tables."""
    try:
        return await sync_manager.get_sync_status()
    except Exception as e:
        raise AppException(f"Failed to get sync status: {str(e)}")


@router.get("/sync/analyze/{dataset_id}/{table_id}")
async def analyze_table(
    dataset_id: str,
    table_id: str,
    sync_manager: PandasGBQSync = Depends(get_sync_manager),
):
    """Analyze a specific synced table."""
    try:
        result = await sync_manager.analyze_table(dataset_id, table_id)
        if "status" in result and result["status"] == "error":
            raise AppException(result["message"])
        return result
    except Exception as e:
        raise AppException(f"Table analysis failed: {str(e)}")


@router.get("/datasets/{dataset_id}/stats", response_model=DatasetStats)
async def get_dataset_stats(
    dataset_id: str,
    processor: QueryProcessor = Depends(get_processor),
) -> DatasetStats:
    """Get basic statistics for a dataset."""
    try:
        query = f"""
        SELECT
            COUNT(*) as table_count,
            MAX(last_modified_time) as last_modified,
            SUM(size_bytes) as total_size_bytes,
            MIN(creation_time) as created,
            ANY_VALUE(dataset_description) as description,
            ANY_VALUE(TO_JSON_STRING(labels)) as labels
        FROM `{dataset_id}.__TABLES__`
        """
        df = await processor.execute_gbq_query(query)

        if df.empty:
            raise AppException(f"Dataset {dataset_id} not found or is empty")

        row = df.iloc[0]
        labels = (
            {}
            if row["labels"] is None
            else processor.convert_numpy_types(row["labels"])
        )

        return DatasetStats(
            table_count=int(row["table_count"]),
            last_modified=str(row["last_modified"]),
            total_size_bytes=int(row["total_size_bytes"]),
            created=str(row["created"]),
            description=row["description"],
            labels=labels,
        )

    except Exception as e:
        raise AppException(f"Error fetching dataset statistics: {str(e)}")
