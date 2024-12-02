import pandas_gbq
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy import create_engine, MetaData, inspect

from app.config.credentials import CredentialsInfo

class PandasGBQSync:
    def __init__(self, creds: CredentialsInfo, database_url: str):
        self.project_id = creds.project_id
        self.credentials = creds.credentials
        self.engine = create_engine(database_url)
        self.metadata = MetaData()
        
        pandas_gbq.context.credentials = self.credentials
        pandas_gbq.context.project = self.project_id

    async def sync_table(
        self,
        dataset_id: str,
        table_id: str,
        chunksize: int = 10000,
        if_exists: str = 'replace'
    ) -> Dict:
        """
        Sync a single table from BigQuery to PostgreSQL using pandas-gbq
        """
        start_time = datetime.now()
        
        try:
            # Construct the query
            query = f"""
            SELECT *
            FROM `{self.project_id}.{dataset_id}.{table_id}`
            """
            
            # Get the row count first
            count_query = f"""
            SELECT COUNT(*) as count
            FROM `{self.project_id}.{dataset_id}.{table_id}`
            """
            count_df = pandas_gbq.read_gbq(count_query, project_id=self.project_id)
            total_rows = count_df['count'].iloc[0]
            
            if total_rows == 0:
                return {
                    "status": "success",
                    "message": "Table is empty",
                    "rows_synced": 0,
                    "duration": str(datetime.now() - start_time)
                }
            
            # For large tables, use chunking
            if total_rows > chunksize:
                offset = 0
                while offset < total_rows:
                    chunk_query = f"""
                    {query}
                    LIMIT {chunksize}
                    OFFSET {offset}
                    """
                    
                    chunk_df = pandas_gbq.read_gbq(chunk_query, project_id=self.project_id)
                    
                    # Write to PostgreSQL
                    chunk_df.to_sql(
                        name=table_id,
                        schema=dataset_id,
                        con=self.engine,
                        if_exists='append' if offset > 0 else if_exists,
                        index=False,
                        method='multi',
                        chunksize=1000  # Chunk size for PostgreSQL insertion
                    )
                    
                    offset += chunksize
            else:
                # For smaller tables, sync all at once
                df = pandas_gbq.read_gbq(query, project_id=self.project_id)
                df.to_sql(
                    name=table_id,
                    schema=dataset_id,
                    con=self.engine,
                    if_exists=if_exists,
                    index=False,
                    method='multi'
                )
            
            # Create indices if needed
            self._create_indices(dataset_id, table_id, df.columns)
            
            return {
                "status": "success",
                "message": f"Synced {total_rows} rows",
                "rows_synced": total_rows,
                "duration": str(datetime.now() - start_time)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "duration": str(datetime.now() - start_time)
            }

    def _create_indices(self, dataset_id: str, table_id: str, columns: pd.Index):
        """Create useful indices based on column types"""
        with self.engine.connect() as conn:
            # Get column types
            insp = inspect(self.engine)
            col_types = {col['name']: col['type'] 
                        for col in insp.get_columns(table_id, schema=dataset_id)}
            
            # Create indices for likely join/filter columns
            for col in columns:
                try:
                    # Create index for ID-like columns
                    if any(key in col.lower() for key in ['id', 'key', 'code']):
                        idx_name = f"idx_{dataset_id}_{table_id}_{col}"
                        conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS {idx_name}
                        ON {dataset_id}.{table_id} ({col})
                        """)
                        
                    # Create index for date columns
                    elif 'date' in col.lower() or 'time' in col.lower():
                        idx_name = f"idx_{dataset_id}_{table_id}_{col}"
                        conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS {idx_name}
                        ON {dataset_id}.{table_id} ({col})
                        """)
                except Exception as e:
                    print(f"Failed to create index for {col}: {str(e)}")

    async def sync_dataset(
        self,
        dataset_id: str,
        exclude_tables: Optional[List[str]] = None
    ) -> Dict:
        """Sync all tables in a dataset"""
        start_time = datetime.now()
        exclude_tables = exclude_tables or []
        
        try:
            # Get list of tables
            query = f"""
            SELECT table_id
            FROM `{self.project_id}.{dataset_id}.__TABLES__`
            """
            tables_df = pandas_gbq.read_gbq(query, project_id=self.project_id)
            
            results = []
            for table_id in tables_df['table_id']:
                if table_id not in exclude_tables:
                    result = await self.sync_table(dataset_id, table_id)
                    results.append({
                        "table_id": table_id,
                        **result
                    })
            
            return {
                "status": "success",
                "tables_synced": len(results),
                "results": results,
                "duration": str(datetime.now() - start_time)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "duration": str(datetime.now() - start_time)
            }

    async def get_sync_status(self) -> List[Dict]:
        """Get sync status of all tables"""
        query = """
        SELECT 
            schemaname as dataset_id,
            tablename as table_id,
            pg_size_pretty(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename))) as size,
            n_live_tup as row_count,
            last_vacuum as last_sync,
            last_analyze as last_analyzed
        FROM pg_stat_user_tables
        ORDER BY dataset_id, table_id;
        """
        
        with self.engine.connect() as conn:
            result = pd.read_sql(query, conn)
            return result.to_dict(orient='records')

    async def analyze_table(self, dataset_id: str, table_id: str) -> Dict:
        """Get detailed statistics about a synced table"""
        try:
            with self.engine.connect() as conn:
                # Get basic stats
                stats_query = f"""
                SELECT 
                    pg_size_pretty(pg_total_relation_size('{dataset_id}.{table_id}')) as total_size,
                    pg_size_pretty(pg_table_size('{dataset_id}.{table_id}')) as table_size,
                    pg_size_pretty(pg_indexes_size('{dataset_id}.{table_id}')) as index_size,
                    n_live_tup as row_count,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_analyze
                FROM pg_stat_user_tables 
                WHERE schemaname = '{dataset_id}' AND tablename = '{table_id}'
                """
                stats = pd.read_sql(stats_query, conn).to_dict(orient='records')[0]
                
                # Get column statistics
                cols_query = f"""
                SELECT 
                    column_name,
                    data_type,
                    pg_size_pretty(pg_column_size({dataset_id}.{table_id}.*)) as estimated_size
                FROM information_schema.columns
                WHERE table_schema = '{dataset_id}' 
                AND table_name = '{table_id}'
                GROUP BY column_name, data_type
                """
                columns = pd.read_sql(cols_query, conn).to_dict(orient='records')
                
                return {
                    "table_stats": stats,
                    "columns": columns
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def execute_query(self, query: str) -> pd.DataFrame:
        """Execute a BigQuery query and return the result as a DataFrame"""
        return pandas_gbq.read_gbq(query, project_id=self.project_id)