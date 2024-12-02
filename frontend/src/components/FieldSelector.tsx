import React from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { VStack, HStack, IconButton, Text, useColorMode } from '@chakra-ui/react';
import { DragHandleIcon, DeleteIcon, AddIcon } from '@chakra-ui/icons';
import { FieldSelectorProps } from './types';
import { DropResult } from 'react-beautiful-dnd';

const FieldSelector: React.FC<FieldSelectorProps> = ({
    fields,
    selectedFields,
    onFieldSelect,
    onFieldRemove,
    onFieldReorder
}) => {
    const { colorMode } = useColorMode();
    
    const handleDragEnd = (result: DropResult) => {
        if (!result.destination) return;
        onFieldReorder(result.source.index, result.destination.index);
    };
    
    return (
        <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="fields">
                {(provided) => (
                    <VStack
                        {...provided.droppableProps}
                        ref={provided.innerRef}
                        align="stretch"
                        spacing={2}
                    >
                        {fields.map((field, index) => (
                            <Draggable
                                key={field.name}
                                draggableId={field.name}
                                index={index}
                            >
                                {(provided, snapshot) => (
                                    <HStack
                                        ref={provided.innerRef}
                                        {...provided.draggableProps}
                                        {...provided.dragHandleProps}
                                        p={2}
                                        bg={colorMode === 'dark' ? 'gray.700' : 'gray.100'}
                                        borderRadius="md"
                                        justify="space-between"
                                        opacity={snapshot.isDragging ? 0.8 : 1}
                                        shadow={snapshot.isDragging ? 'lg' : 'none'}
                                    >
                                        <DragHandleIcon />
                                        <Text flex={1}>{field.name}</Text>
                                        <Text color="gray.500" fontSize="sm">{field.type}</Text>
                                        {selectedFields.some(sf => sf.fieldName === field.name) ? (
                                            <IconButton
                                                aria-label="Remove field"
                                                size="sm"
                                                icon={<DeleteIcon />}
                                                onClick={() => onFieldRemove(field.name)}
                                            />
                                        ) : (
                                            <IconButton
                                                aria-label="Add field"
                                                size="sm"
                                                icon={<AddIcon />}
                                                onClick={() => onFieldSelect({
                                                    fieldName: field.name,
                                                })}
                                            />
                                        )}
                                    </HStack>
                                )}
                            </Draggable>
                        ))}
                        {provided.placeholder}
                    </VStack>
                )}
            </Droppable>
        </DragDropContext>
    );
};

export default FieldSelector;