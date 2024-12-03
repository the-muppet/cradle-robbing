from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field

# Base field and schema models
class DatabaseField(BaseModel):
    name: str = Field(..., min_length=1)
    type: str 
    description: Optional[str] = None
    nullable: Optional[bool] = None

class ForeignKeyConstraint(BaseModel):
    columns: List[str]
    reference_table: str = Field(..., min_length=1)
    reference_columns: List[str]

class TableSchema(BaseModel):
    fields: List[DatabaseField]
    primary_key: Optional[List[str]] = None
    foreign_keys: Optional[List[ForeignKeyConstraint]] = None

# Query types
AggregationType = Literal["COUNT", "SUM", "AVG", "MIN", "MAX", "GROUP_CONCAT"]
ComparisonOperator = Literal["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN"]
JoinType = Literal["INNER", "LEFT", "RIGHT", "FULL"]
Conjunction = Literal["AND", "OR"]

# Query builder models
class QueryField(BaseModel):
    field_name: str = Field(..., min_length=1)
    alias: Optional[str] = None
    table_alias: Optional[str] = None
    expression: Optional[str] = None
    aggregation: Optional[AggregationType] = None

class JoinCondition(BaseModel):
    left_field: str
    right_field: str
    operator: ComparisonOperator

class JoinClause(BaseModel):
    type: JoinType
    table: str = Field(..., min_length=1)
    table_alias: str
    conditions: List[JoinCondition]

class WhereCondition(BaseModel):
    field: str
    operator: ComparisonOperator
    value: Any
    is_field: Optional[bool] = False

class WhereClause(BaseModel):
    conditions: List[WhereCondition]
    conjunction: Conjunction

class GroupByClause(BaseModel):
    fields: List[str]
    having: Optional[WhereClause] = None

class OrderByClause(BaseModel):
    field: str
    direction: Literal["ASC", "DESC"]

class QueryBuilderState(BaseModel):
    selected_fields: List[QueryField]
    joins: List[JoinClause]
    where: Optional[WhereClause] = None
    group_by: Optional[GroupByClause] = None
    order_by: Optional[List[OrderByClause]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    distinct: bool = False

# API models
class QueryRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    dataset_id: str = Field(..., min_length=1)
    query: str
    auto_alias: Optional[bool] = False
    parameters: Optional[Dict[str, Any]] = None

class TableInfo(BaseModel):
    row_count: int = Field(..., ge=0)
    column_schema: List[DatabaseField]
    preview: List[Dict[str, Any]]

class QueryResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    rows: List[Dict[str, Any]]
    column_schema: List[DatabaseField]
    total_rows: int = Field(..., ge=0)

class QueryValidationError(BaseModel):
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    severity: Literal["ERROR", "WARNING", "INFO"]

class SyncResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None

class SyncTableRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1)
    table_id: str = Field(..., min_length=1) 
    chunksize: int = Field(default=10000, gt=0)

class SyncDatasetRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1)
    exclude_tables: Optional[List[str]] = None

class HealthResponse(BaseModel):
    status: str
    bigquery: str

class DatasetStats(BaseModel):
    table_count: int
    last_modified: str
    total_size_bytes: int
    created: str
    description: Optional[str] = None
    labels: Dict[str, str]