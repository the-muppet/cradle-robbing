
export interface QueryEditorProps {
        query: string;
        setQuery: (query: string) => void;
        onRun: () => void;
        isLoading: boolean;
    }

export const QueryEditor: React.ComponentType<QueryEditorProps>;


export interface TableField {
    name: string;
    type: string;
}

export interface TableInfo {
    row_count: number;
    schema: TableField[];
    preview: Record<string, any>[];
}

export interface ResultsViewProps {
    tableInfo?: TableInfo;
    queryResults?: any;
    onFieldClick: (fieldName: string) => void;
    isLoading: boolean;
}

export interface DatabaseField {
    name: string;
    type: string;
    description?: string;
    nullable?: boolean;
}

export interface TableSchema {
    fields: DatabaseField[];
    primaryKey?: string[];
    foreignKeys?: ForeignKeyConstraint[];
}

export interface ForeignKeyConstraint {
    columns: string[];
    referenceTable: string;
    referenceColumns: string[];
}

// Query Builder specific types
export interface QueryField {
    fieldName: string;
    alias?: string;
    tableAlias?: string;
    expression?: string;
    aggregation?: AggregationType;
}

export type AggregationType = 'COUNT' | 'SUM' | 'AVG' | 'MIN' | 'MAX' | 'GROUP_CONCAT';

export interface JoinClause {
    type: 'INNER' | 'LEFT' | 'RIGHT' | 'FULL';
    table: string;
    tableAlias: string;
    conditions: JoinCondition[];
}

export interface JoinCondition {
    leftField: string;
    rightField: string;
    operator: ComparisonOperator;
}

export type ComparisonOperator = '=' | '!=' | '>' | '<' | '>=' | '<=' | 'LIKE' | 'IN';

export interface WhereClause {
    conditions: WhereCondition[];
    conjunction: 'AND' | 'OR';
}

export interface WhereCondition {
    field: string;
    operator: ComparisonOperator;
    value: any;
    isField?: boolean;  // If true, value is treated as a field reference
}

export interface GroupByClause {
    fields: string[];
    having?: WhereClause;
}

export interface OrderByClause {
    field: string;
    direction: 'ASC' | 'DESC';
}

export interface QueryBuilderState {
    selectedFields: QueryField[];
    joins: JoinClause[];
    where?: WhereClause;
    groupBy?: GroupByClause;
    orderBy?: OrderByClause[];
    limit?: number;
    offset?: number;
    distinct: boolean;
}

// Component Props interfaces
export interface QueryBuilderProps {
    tableInfo: TableInfo;
    initialState?: QueryBuilderState;
    onQueryChange: (query: string) => void;
    onStateChange?: (state: QueryBuilderState) => void;
}

export interface FieldSelectorProps {
    fields: DatabaseField[];
    selectedFields: QueryField[];
    onFieldSelect: (field: QueryField) => void;
    onFieldRemove: (fieldName: string) => void;
    onFieldReorder: (startIndex: number, endIndex: number) => void;
}

export interface JoinBuilderProps {
    availableTables: string[];
    currentJoins: JoinClause[];
    onJoinAdd: (join: JoinClause) => void;
    onJoinRemove: (index: number) => void;
    onJoinUpdate: (index: number, join: JoinClause) => void;
}

// Drag and drop types
export interface DraggableFieldItem {
    id: string;
    type: 'FIELD' | 'AGGREGATION' | 'EXPRESSION';
    content: QueryField;
}

export interface DropResult {
    source: {
        index: number;
        droppableId: string;
    };
    destination?: {
        index: number;
        droppableId: string;
    };
    draggableId: string;
}

// API types
export interface QueryRequest {
    dataset_id: string;
    query: string;
    auto_alias?: boolean;
    parameters?: Record<string, any>;
}

export interface QueryResponse {
    rows: any[];
    columnSchema: DatabaseField[];
    total_rows: number;
}

// Table Information types
export interface TableInfo {
    row_count: number;
    tableSchema: DatabaseField[];
    preview: Record<string, any>[];
}

// Error handling types
export interface QueryValidationError {
    message: string;
    line?: number;
    column?: number;
    severity: 'ERROR' | 'WARNING' | 'INFO';
}

export interface QueryBuilderError extends Error {
    type: 'VALIDATION' | 'EXECUTION' | 'SYSTEM';
    details?: QueryValidationError[];
}

export interface TableSelectorProps {
    isOpen: boolean;
    onClose: () => void;
    tables: string[];
    onSelect: (table: string) => void;
    selectedTable?: string;
    title?: string;
}

export interface ParsedTable {
    name: string;
    year?: string;
    month?: string;
    day?: string;
    type?: string;
}

export interface TableField {
    name: string;
    type: string;
}

export interface TableInfo {
    row_count: number;
    schema: TableField[];
    preview: Record<string, any>[];
}

export interface ResultsViewProps {
    tableInfo?: TableInfo;
    queryResults?: any;
    onFieldClick: (fieldName: string) => void;
    isLoading?: boolean;
}

export interface ImportMetaEnv {
    readonly VITE_API_URL: string;
}

declare global {
    interface ImportMeta {
        env: ImportMetaEnv;
    }
}

export interface TableField {
    name: string;
    type: string;
}

export interface TableInfo {
    row_count: number;
    schema: TableField[];
    preview: Record<string, any>[];
}

export interface TableGroup {
    year: string;
    months: {
        [key: string]: string[];
    };
}

export interface DatasetGroup {
    category: string;
    datasets: string[];
}

export interface DatasetStats {
    table_count: number;
    last_modified: string;
    total_size_bytes: number;
    created: string;
    description: string | null;
    labels: Record<string, string>;
}

export interface QueryEditorProps {
    query: string;
    setQuery: (query: string) => void;
    onRun: () => void;
    isLoading: boolean;
}