import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalBody,
    ModalCloseButton,
    Input,
    InputGroup,
    InputLeftElement,
    VStack,
    Text,
    useColorMode,
    Box,
    Badge,
    HStack,
    Kbd,
    Tooltip,
} from '@chakra-ui/react'
import { SearchIcon, CalendarIcon, TimeIcon } from '@chakra-ui/icons'
import { useState, useMemo, useEffect } from 'react'
import type { TableSelectorProps, ParsedTable } from './types'

export default function TableSelector({ isOpen, onClose, tables, onSelect, selectedTable, title }: TableSelectorProps) {
    const [search, setSearch] = useState('')
    const [selectedIndex, setSelectedIndex] = useState(0)
    const { colorMode } = useColorMode()

    const parseTableName = (table: string): ParsedTable => {
        const parts = table.split('_')
        const result: ParsedTable = { name: table }

        if (parts.length >= 3) {
            const [year, month, day, ...rest] = parts
            if (!isNaN(Number(year)) && !isNaN(Number(month)) && !isNaN(Number(day))) {
                result.year = year
                result.month = month
                result.day = day
                result.type = rest.join('_')
            }
        }

        return result
    }

    const filteredTables = useMemo(() => {
        return tables
            .map(parseTableName)
            .filter(table => {
                const searchLower = search.toLowerCase()
                return (
                    table.name.toLowerCase().includes(searchLower) ||
                    table.type?.toLowerCase().includes(searchLower) ||
                    `${table.year}-${table.month}-${table.day}`.includes(searchLower)
                )
            })
            .sort((a, b) => {
                // Sort by date if both have dates
                if (a.year && b.year) {
                    return b.name.localeCompare(a.name)
                }
                return a.name.localeCompare(b.name)
            })
    }, [tables, search])

    // Keyboard navigation
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (!isOpen) return

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault()
                    setSelectedIndex(i => Math.min(i + 1, filteredTables.length - 1))
                    break
                case 'ArrowUp':
                    e.preventDefault()
                    setSelectedIndex(i => Math.max(i - 1, 0))
                    break
                case 'Enter':
                    e.preventDefault()
                    if (filteredTables[selectedIndex]) {
                        onSelect(filteredTables[selectedIndex].name)
                        onClose()
                    }
                    break
                case 'Escape':
                    e.preventDefault()
                    onClose()
                    break
            }
        }

        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [isOpen, filteredTables, selectedIndex, onSelect, onClose])

    // Reset selection when search changes
    useEffect(() => {
        setSelectedIndex(0)
    }, [search])

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="xl">
            <ModalOverlay backdropFilter="blur(10px)" />
            <ModalContent bg={colorMode === 'dark' ? 'gray.800' : 'white'}>
                <ModalHeader>
                    <HStack justify="space-between">
                        <Text
                            color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}
                            fontWeight="bold"
                        >
                            {title || 'Select Table'}
                        </Text>
                        <HStack spacing={2}>
                            <Kbd>↑↓</Kbd>
                            <Text fontSize="sm">to navigate</Text>
                            <Kbd>enter</Kbd>
                            <Text fontSize="sm">to select</Text>
                        </HStack>
                    </HStack>
                </ModalHeader>
                <ModalCloseButton />
                <ModalBody pb={6}>
                    <VStack spacing={4} align="stretch">
                        <InputGroup>
                            <InputLeftElement pointerEvents="none">
                                <SearchIcon color={colorMode === 'dark' ? 'primary.300' : 'primary.600'} />
                            </InputLeftElement>
                            <Input
                                placeholder="Search by name or date (YYYY-MM-DD)..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                bg={colorMode === 'dark' ? 'gray.700' : 'white'}
                                borderColor={colorMode === 'dark' ? 'gray.600' : 'gray.200'}
                                _focus={{
                                    borderColor: colorMode === 'dark' ? 'primary.500' : 'primary.400',
                                    boxShadow: `0 0 0 1px ${colorMode === 'dark' ? 'primary.500' : 'primary.400'}`
                                }}
                                autoFocus
                            />
                        </InputGroup>
                        <Box maxH="60vh" overflowY="auto" {...scrollbarStyles(colorMode)}>
                            <VStack spacing={2} align="stretch">
                                {filteredTables.map((table, index) => (
                                    <Box
                                        key={table.name}
                                        p={2}
                                        cursor="pointer"
                                        borderRadius="md"
                                        bg={
                                            selectedIndex === index || selectedTable === table.name
                                                ? (colorMode === 'dark' ? 'gray.700' : 'primary.50')
                                                : 'transparent'
                                        }
                                        _hover={{
                                            bg: colorMode === 'dark' ? 'gray.700' : 'primary.50'
                                        }}
                                        onClick={() => {
                                            onSelect(table.name)
                                            onClose()
                                        }}
                                    >
                                        <HStack spacing={2}>
                                            {table.year ? (
                                                <Tooltip
                                                    label={`Created on ${table.year}-${table.month}-${table.day}`}
                                                    placement="top"
                                                >
                                                    <CalendarIcon color={colorMode === 'dark' ? 'primary.300' : 'primary.600'} />
                                                </Tooltip>
                                            ) : (
                                                <TimeIcon color={colorMode === 'dark' ? 'primary.300' : 'primary.600'} />
                                            )}
                                            <Text color={colorMode === 'dark' ? 'gray.100' : 'gray.800'}>
                                                {table.type || table.name}
                                            </Text>
                                            {table.year && (
                                                <Badge
                                                    colorScheme="primary"
                                                    ml="auto"
                                                >
                                                    {table.year}-{table.month}-{table.day}
                                                </Badge>
                                            )}
                                        </HStack>
                                    </Box>
                                ))}
                            </VStack>
                        </Box>
                    </VStack>
                </ModalBody>
            </ModalContent>
        </Modal>
    )
}

const scrollbarStyles = (colorMode: string) => ({
    css: {
        '&::-webkit-scrollbar': {
            width: '4px',
        },
        '&::-webkit-scrollbar-track': {
            width: '6px',
        },
        '&::-webkit-scrollbar-thumb': {
            background: colorMode === 'dark' ? '#4d7a68' : '#9abcad',
            borderRadius: '24px',
        },
    }
}) 