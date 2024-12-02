declare module './QueryEditor' {
    interface QueryEditorProps {
        query: string;
        setQuery: (query: string) => void;
        onRun: () => void;
        isLoading: boolean;
    }
    const QueryEditor: React.ComponentType<QueryEditorProps>
    export default QueryEditor
}

declare module './ResultsView' {
    interface TableField {
        name: string;
        type: string;
    }
    interface TableInfo {
        row_count: number;
        schema: TableField[];
        preview: Record<string, any>[];
    }
    interface ResultsViewProps {
        tableInfo?: TableInfo;
        queryResults?: any;
        onFieldClick: (fieldName: string) => void;
    }
    const ResultsView: React.ComponentType<ResultsViewProps>
    export default ResultsView
} 