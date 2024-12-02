import {
    Card,
    CardHeader,
    CardBody,
    Heading,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Badge,
    Button,
    Tabs,
    TabList,
    Tab,
    TabPanels,
    TabPanel,
    useColorMode,
    Box,
    Wrap,
    WrapItem,
    HStack,
    Spinner,
} from '@chakra-ui/react'
import { Key } from 'react';
import { TableField, ResultsViewProps } from './types';

function ResultsView({ tableInfo, queryResults, onFieldClick, isLoading }: ResultsViewProps) {
    const { colorMode } = useColorMode()

    return (
        <Card variant="glass">
            <CardHeader>
                <HStack justify="space-between">
                    <Heading size="md">Results</Heading>
                    {isLoading && <Spinner size="sm" color="primary.500" />}
                </HStack>
            </CardHeader>
            <CardBody>
                <Tabs>
                    <TabList borderColor={colorMode === 'dark' ? 'gray.700' : 'gray.200'}>
                        <Tab
                            color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}
                            _selected={{
                                color: colorMode === 'dark' ? 'primary.100' : 'primary.800',
                                borderColor: colorMode === 'dark' ? 'primary.500' : 'primary.400'
                            }}
                        >
                            Schema
                        </Tab>
                        <Tab
                            color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}
                            _selected={{
                                color: colorMode === 'dark' ? 'primary.100' : 'primary.800',
                                borderColor: colorMode === 'dark' ? 'primary.500' : 'primary.400'
                            }}
                        >
                            Data Preview
                        </Tab>
                        {queryResults && (
                            <Tab
                                color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}
                                _selected={{
                                    color: colorMode === 'dark' ? 'primary.100' : 'primary.800',
                                    borderColor: colorMode === 'dark' ? 'primary.500' : 'primary.400'
                                }}
                            >
                                Query Results ({queryResults.total_rows} rows)
                            </Tab>
                        )}
                    </TabList>
                    <TabPanels>
                        <TabPanel>
                            <Wrap spacing={4}>
                                {(queryResults?.schema || tableInfo?.schema)?.map((field: TableField) => (
                                    <WrapItem key={field.name}>
                                        <Box
                                            p={2}
                                            borderRadius="md"
                                            bg={colorMode === 'dark' ? 'rgba(30, 30, 30, 0.8)' : 'rgba(255, 255, 255, 0.85)'}
                                            borderWidth="1px"
                                            borderColor={colorMode === 'dark' ? 'gray.700' : 'gray.200'}
                                            transition="all 0.2s"
                                            _hover={{
                                                transform: 'translateY(-2px)',
                                                boxShadow: colorMode === 'dark'
                                                    ? '0 4px 20px rgba(0, 0, 0, 0.15)'
                                                    : '0 4px 20px rgba(0, 0, 0, 0.08)',
                                            }}
                                        >
                                            <HStack spacing={2}>
                                                <Button
                                                    variant="link"
                                                    onClick={() => onFieldClick(field.name)}
                                                    color={colorMode === 'dark' ? 'primary.300' : 'primary.600'}
                                                    _hover={{
                                                        transform: 'translateX(4px)',
                                                        color: colorMode === 'dark' ? 'primary.400' : 'primary.500'
                                                    }}
                                                >
                                                    {field.name}
                                                </Button>
                                                <Badge
                                                    colorScheme="primary"
                                                    px={2}
                                                    py={1}
                                                    borderRadius="full"
                                                >
                                                    {field.type}
                                                </Badge>
                                            </HStack>
                                        </Box>
                                    </WrapItem>
                                ))}
                            </Wrap>
                        </TabPanel>
                        <TabPanel>
                            <Box
                                borderRadius="md"
                                overflow="hidden"
                                bg={colorMode === 'dark' ? 'rgba(30, 30, 30, 0.8)' : 'rgba(255, 255, 255, 0.85)'}
                            >
                                <Table>
                                    <Thead>
                                        <Tr>
                                            {Object.keys((queryResults?.rows?.[0] || tableInfo?.preview?.[0] || {})).map(key => (
                                                <Th key={key}>{key}</Th>
                                            ))}
                                        </Tr>
                                    </Thead>
                                    <Tbody>
                                        {(queryResults?.rows || tableInfo?.preview)?.map((row: Record<string, any>, i: number) => (
                                            <Tr key={i}>
                                                {Object.values(row).map((value, j) => (
                                                    <Td key={j}>{String(value)}</Td>
                                                ))}
                                            </Tr>
                                        ))}
                                    </Tbody>
                                </Table>
                            </Box>
                        </TabPanel>
                        {queryResults && (
                            <TabPanel>
                                <Box
                                    borderRadius="md"
                                    overflow="auto"
                                    maxH="60vh"
                                    bg={colorMode === 'dark' ? 'rgba(30, 30, 30, 0.8)' : 'rgba(255, 255, 255, 0.85)'}
                                    css={{
                                        '&::-webkit-scrollbar': {
                                            width: '8px',
                                            height: '8px',
                                        },
                                        '&::-webkit-scrollbar-track': {
                                            background: colorMode === 'dark' ? 'rgba(0, 0, 0, 0.2)' : 'rgba(0, 0, 0, 0.05)',
                                        },
                                        '&::-webkit-scrollbar-thumb': {
                                            background: colorMode === 'dark' ? 'primary.700' : 'primary.200',
                                            borderRadius: '4px',
                                        },
                                    }}
                                >
                                    <Table size="sm">
                                        <Thead position="sticky" top={0} bg={colorMode === 'dark' ? 'gray.800' : 'white'}>
                                            <Tr>
                                                {Object.keys(queryResults.rows[0] || {}).map(key => (
                                                    <Th 
                                                        key={key}
                                                        color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}
                                                        borderColor={colorMode === 'dark' ? 'gray.700' : 'gray.200'}
                                                        whiteSpace="nowrap"
                                                    >
                                                        {key}
                                                    </Th>
                                                ))}
                                            </Tr>
                                        </Thead>
                                        <Tbody>
                                            {queryResults.rows.map((row: { [s: string]: unknown; } | ArrayLike<unknown>, i: Key | null | undefined) => (
                                                <Tr 
                                                    key={i}
                                                    _hover={{
                                                        bg: colorMode === 'dark' ? 'gray.700' : 'gray.50'
                                                    }}
                                                >
                                                    {Object.values(row).map((value, j) => (
                                                        <Td 
                                                            key={j}
                                                            borderColor={colorMode === 'dark' ? 'gray.700' : 'gray.200'}
                                                            whiteSpace="nowrap"
                                                        >
                                                            {String(value)}
                                                        </Td>
                                                    ))}
                                                </Tr>
                                            ))}
                                        </Tbody>
                                    </Table>
                                </Box>
                            </TabPanel>
                        )}
                    </TabPanels>
                </Tabs>
            </CardBody>
        </Card>
    )
};

export default ResultsView;