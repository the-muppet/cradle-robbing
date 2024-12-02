import React, { useState, useCallback } from 'react';
import {
    Box,
    VStack,
    HStack,
    Switch,
    FormControl,
    FormLabel,
} from '@chakra-ui/react';
import type {
    QueryBuilderProps,
    QueryField,
    QueryBuilderState
} from './types';
import FieldSelector from './FieldSelector';

const QueryBuilder: React.FC<QueryBuilderProps> = ({
    tableInfo,
    initialState,
    onQueryChange,
    onStateChange
}) => {
    const [state, setState] = useState<QueryBuilderState>(initialState || {
        selectedFields: [],
        joins: [],
        distinct: false
    });
    const [autoAlias, setAutoAlias] = useState(true);
    
    const updateQueryFromState = useCallback((newState: QueryBuilderState) => {
        if (newState.selectedFields.length === 0) {
            onQueryChange('');
            return;
        }
        
        const fieldList = newState.selectedFields
            .map(field => {
                const fieldRef = field.tableAlias 
                    ? `${field.tableAlias}.${field.fieldName}`
                    : field.fieldName;
                    
                if (autoAlias) {
                    const alias = field.alias || `${field.fieldName}_${field.tableAlias || 'main'}`;
                    return `${fieldRef} AS ${alias}`;
                }
                return fieldRef;
            })
            .join(',\n  ');
            
        let query = `SELECT${state.distinct ? ' DISTINCT' : ''}\n  ${fieldList}\nFROM \${TABLE}`;
        
        // Add joins if present
        if (newState.joins.length > 0) {
            query += '\n' + newState.joins
                .map(join => `${join.type} JOIN ${join.table} AS ${join.tableAlias} ON ${
                    join.conditions
                        .map(cond => `${cond.leftField} ${cond.operator} ${cond.rightField}`)
                        .join(' AND ')
                }`)
                .join('\n');
        }
        
        // Add where clause if present
        if (newState.where && newState.where.conditions.length > 0) {
            query += `\nWHERE ${newState.where.conditions
                .map(cond => `${cond.field} ${cond.operator} ${
                    cond.isField ? cond.value : JSON.stringify(cond.value)
                }`)
                .join(` ${newState.where.conjunction} `)}`;
        }
        
        // Add group by if present
        if (newState.groupBy && newState.groupBy.fields.length > 0) {
            query += `\nGROUP BY ${newState.groupBy.fields.join(', ')}`;
            
            if (newState.groupBy.having) {
                query += `\nHAVING ${newState.groupBy.having.conditions
                    .map(cond => `${cond.field} ${cond.operator} ${
                        cond.isField ? cond.value : JSON.stringify(cond.value)
                    }`)
                    .join(` ${newState.groupBy.having.conjunction} `)}`;
            }
        }
        
        // Add order by if present
        if (newState.orderBy && newState.orderBy.length > 0) {
            query += `\nORDER BY ${newState.orderBy
                .map(order => `${order.field} ${order.direction}`)
                .join(', ')}`;
        }
        
        // Add limit and offset if present
        if (newState.limit) {
            query += `\nLIMIT ${newState.limit}`;
            if (newState.offset) {
                query += `\nOFFSET ${newState.offset}`;
            }
        }
        
        onQueryChange(query);
        onStateChange?.(newState);
    }, [state.distinct, autoAlias, onQueryChange, onStateChange]);
    
    const handleFieldSelect = (field: QueryField) => {
        const newState = {
            ...state,
            selectedFields: [...state.selectedFields, field]
        };
        setState(newState);
        updateQueryFromState(newState);
    };
    
    const handleFieldRemove = (fieldName: string) => {
        const newState = {
            ...state,
            selectedFields: state.selectedFields.filter(f => f.fieldName !== fieldName)
        };
        setState(newState);
        updateQueryFromState(newState);
    };
    
    const handleFieldReorder = (startIndex: number, endIndex: number) => {
        const newFields = Array.from(state.selectedFields);
        const [removed] = newFields.splice(startIndex, 1);
        newFields.splice(endIndex, 0, removed);
        
        const newState = {
            ...state,
            selectedFields: newFields
        };
        setState(newState);
        updateQueryFromState(newState);
    };
    
    return (
        <Box p={4} borderWidth="1px" borderRadius="lg">
            <VStack spacing={4} align="stretch">
                <HStack spacing={4}>
                    <FormControl display="flex" alignItems="center">
                        <FormLabel mb="0">Auto-alias fields</FormLabel>
                        <Switch
                            isChecked={autoAlias}
                            onChange={(e) => {
                                setAutoAlias(e.target.checked);
                                updateQueryFromState(state);
                            }}
                        />
                    </FormControl>
                    <FormControl display="flex" alignItems="center">
                        <FormLabel mb="0">Distinct</FormLabel>
                        <Switch
                            isChecked={state.distinct}
                            onChange={(e) => {
                                const newState = {
                                    ...state,
                                    distinct: e.target.checked
                                };
                                setState(newState);
                                updateQueryFromState(newState);
                            }}
                        />
                    </FormControl>
                </HStack>
                
                <FieldSelector
                    fields={tableInfo.tableSchema}
                    selectedFields={state.selectedFields}
                    onFieldSelect={handleFieldSelect}
                    onFieldRemove={handleFieldRemove}
                    onFieldReorder={handleFieldReorder}
                />
            </VStack>
        </Box>
    );
};

export default QueryBuilder;