from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from dataclasses import dataclass
from google.oauth2 import service_account

# Base database models
class DatabaseField(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    nullable: Optional[bool] = None

class ForeignKeyConstraint(BaseModel):
    columns: List[str]
    reference_table: str
    reference_columns: List[str]

class TableSchema(BaseModel):
    fields: List[DatabaseField]
    primary_key: Optional[List[str]] = None
    foreign_keys: Optional[List[ForeignKeyConstraint]] = None

# Query builder models
AggregationType = Literal["COUNT", "SUM", "AVG", "MIN", "MAX", "GROUP_CONCAT"]
ComparisonOperator = Literal["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN"]
JoinType = Literal["INNER", "LEFT", "RIGHT", "FULL"]
Conjunction = Literal["AND", "OR"]

class QueryField(BaseModel):
    field_name: str
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
    table: str
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

# API request/response models
class QueryRequest(BaseModel):
    dataset_id: str
    query: str
    auto_alias: Optional[bool] = False
    parameters: Optional[Dict[str, Any]] = None

class TableInfo(BaseModel):
    row_count: int
    table_schema: List[DatabaseField] = Field(..., alias="schema")
    preview: List[Dict[str, Any]]

class QueryResponse(BaseModel):
    rows: List[Dict[str, Any]]
    table_schema: List[DatabaseField] = Field(..., alias="schema")
    total_rows: int

class QueryValidationError(BaseModel):
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    severity: Literal["ERROR", "WARNING", "INFO"]

class ColumnSchema(BaseModel):
    name: str
    type: str

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    rows: List[Dict[str, Any]]
    schema: List[ColumnSchema]
    total_rows: int

class SyncResponse(BaseModel):
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None

class SyncTableRequest(BaseModel):
    dataset_id: str
    table_id: str
    chunksize: int = Field(default=10000, gt=0)

class SyncDatasetRequest(BaseModel):
    dataset_id: str
    exclude_tables: Optional[List[str]] = None