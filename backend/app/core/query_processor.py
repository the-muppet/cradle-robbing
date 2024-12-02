import re
import json
import asyncio
import pandas_gbq
import numpy as np
from fastapi import HTTPException

from app.database.models import QueryResponse
from backend.app.config.credentials import CredentialsInfo


class QueryProcessor:
    def __init__(self, creds: CredentialsInfo):
        self.credentials = creds.credentials
        self.project_id = creds.project_id

    @staticmethod
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
            return {
                key: QueryProcessor.convert_numpy_types(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [QueryProcessor.convert_numpy_types(item) for item in obj]
        return obj

    def qualify_table_references(self, query: str) -> str:
        """Add project ID to unqualified table references."""
        pattern = r"`([^`\.]+\.[^`\.]+)`"

        def replace_match(match):
            table_ref = match.group(1)
            if "." in table_ref and not table_ref.startswith(f"{self.project_id}."):
                return f"`{self.project_id}.{table_ref}`"
            return match.group(0)

        return re.sub(pattern, replace_match, query)

    def generate_alias(self, table_name: str) -> str:
        """Generate a meaningful alias for a table."""
        parts = table_name.split(".")[-1].split("_")
        alias = "".join(word[0] for word in parts if len(word) > 2)
        return alias.lower() or "t"

    async def execute_gbq_query(self, query: str) -> QueryResponse:
        """Execute BigQuery queries with automatic project ID qualification."""
        try:
            qualified_query = self.qualify_table_references(query)
            print(f"Original query: {query}")
            print(f"Qualified query: {qualified_query}")

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: pandas_gbq.read_gbq(
                    qualified_query,
                    project_id=self.project_id,
                    credentials=self.credentials,
                ),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def serialize_dataframe(df):
        """Convert a pandas DataFrame to a JSON-serializable format"""
        records = df.replace({np.nan: None}).to_dict("records")
        return json.loads(
            json.dumps(records, default=QueryProcessor.convert_numpy_types)
        )
