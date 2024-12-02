import { useState, useCallback, Suspense, lazy } from 'react'
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import {
    Grid as ChakraGrid,
    VStack,
    Button,
    Spinner,
    HStack,
    useToast,
    Card,
    CardBody,
    CardHeader,
    Heading,
    IconButton,
    useColorMode,
    Accordion,
    AccordionItem,
    AccordionButton,
    AccordionIcon,
    AccordionPanel,
    SimpleGrid,
    Box,
    Text,
} from '@chakra-ui/react'
import { StarIcon, MoonIcon, SunIcon, ChevronRightIcon } from '@chakra-ui/icons'
import { formatDistance } from 'date-fns'

interface TableField {
    name: string;
    type: string;
}

interface TableInfo {
    row_count: number;
    schema: TableField[];
    preview: Record<string, any>[];
}

interface TableGroup {
    year: string;
    months: {
        [key: string]: string[];
    };
}

interface DatasetGroup {
    category: string;
    datasets: string[];
}

interface DatasetStats {
    table_count: number;
    last_modified: string;
    total_size_bytes: number;
    created: string;
    description: string | null;
    labels: Record<string, string>;
}

const MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getMonthName(monthNum: string): string {
    const num = parseInt(monthNum, 10);
    const monthName = MONTHS[num - 1];
    return monthName !== undefined ? monthName : monthNum;
}

function groupTablesByDate(tables: string[] | undefined): TableGroup[] {
    if (!tables) return [];
    const groups: { [key: string]: { [key: string]: string[] } } = {};
    
    tables?.forEach(table => {
        const parts = table.split('_');
        if (parts.length >= 3) {
            const year = parts[0];
            const month = parts[1];
            
            if (!groups[year]) {
                groups[year] = {};
            }
            if (!groups[year][month]) {
                groups[year][month] = [];
            }
            groups[year][month].push(table);
        }
    });

    return Object.entries(groups)
        .sort((a, b) => b[0].localeCompare(a[0])) // Sort years descending
        .map(([year, months]) => ({
            year,
            months: Object.fromEntries(
                Object.entries(months)
                    .sort((a, b) => {
                        const monthA = parseInt(a[0], 10);
                        const monthB = parseInt(b[0], 10);
                        return monthB - monthA;
                    })
            )
        }));
}

function groupDatasets(datasets: string[] | undefined): DatasetGroup[] {
    if (!datasets) return [];
    const groups: { [key: string]: string[] } = {};
    
    const prefixMap: { [key: string]: string | [key: string] } = {
        'docker_listings': 'Docker Listings',
        'docker_product': 'Docker Products',
        'docker_sellers': 'Docker Sellers',
        'ck': 'Card Kingdom',
        'fab': 'Flesh and Blood',
        'mtg': 'Magic the Gathering',
        'poke': 'Pokemon',
        'ban': 'BAN',
        'yugi': 'Yu-Gi-Oh!',
        'yugioh': 'Yu-Gi-Oh!',
    };
    
    datasets?.forEach(dataset => {
        let category = 'Other';
        let matched = false;
        
        for (const [prefix, categoryName] of Object.entries(prefixMap)) {
            if (dataset.startsWith(prefix)) {
                category = categoryName as string;
                matched = true;
                break;
            }
        }
        
        if (!matched && dataset.includes('_')) {
            const prefix = dataset.split('_')[0];
            category = prefix.charAt(0).toUpperCase() + prefix.slice(1);
        }
        
        if (!groups[category]) {
            groups[category] = [];
        }
        groups[category].push(dataset);
    });

    return Object.entries(groups)
        .sort((a, b) => {
            if (a[0] === 'Other') return 1;
            if (b[0] === 'Other') return -1;
            return a[0].localeCompare(b[0]);
        })
        .map(([category, datasets]) => ({
            category,
            datasets: datasets.sort()
        }));
}

const API_URL = 'http://localhost:8005/api'

const TableSelector = lazy(() => import('./TableSelector'))
const QueryEditor = lazy(() => import('./QueryEditor'))
const ResultsView = lazy(() => import('./ResultsView'))

export default function Explorer() {
    const [selectedDataset, setSelectedDataset] = useState<string>()
    const [selectedTable, setSelectedTable] = useState<string>()
    const [query, setQuery] = useState('')
    const toast = useToast()
    const { colorMode, toggleColorMode } = useColorMode()
    const [selectedMonth, setSelectedMonth] = useState<{year: string, month: string, tables: string[]}>()

    const { data: datasets, isLoading: datasetsLoading } = useQuery<string[], Error, string[]>({
        queryKey: ['datasets'],
        queryFn: async () => {
            const res = await fetch(`${API_URL}/datasets`);
            return res.json() as Promise<string[]>;
        },
        placeholderData: [] as string[],
        gcTime: 30 * 60 * 1000,
        refetchOnMount: false,
        refetchOnWindowFocus: false,
        staleTime: Infinity,
    } as UseQueryOptions<string[], Error, string[]>)

    const queryClient = useQueryClient()
    
    // Prefetch tables when hovering over dataset
    const prefetchTables = useCallback((datasetId: string) => {
        queryClient.prefetchQuery({
            queryKey: ['tables', datasetId],
            queryFn: () => fetch(`${API_URL}/datasets/${datasetId}/tables`).then(res => res.json())
        })
    }, [queryClient])

    const { data: tables, isLoading: tablesLoading } = useQuery<string[]>({
        queryKey: ['tables', selectedDataset],
        queryFn: async () => {
            if (!selectedDataset) return [];
            const res = await fetch(`${API_URL}/datasets/${selectedDataset}/tables`);
            if (!res.ok) {
                throw new Error('Failed to fetch tables');
            }
            return res.json();
        },
        placeholderData: [],
        enabled: !!selectedDataset
    })

    const { data: tableInfo } = useQuery<TableInfo>({
        queryKey: ['tableInfo', selectedDataset, selectedTable],
        queryFn: async () => {
            if (!selectedDataset || !selectedTable) {
                return { row_count: 0, schema: [], preview: [] };
            }
            const res = await fetch(`${API_URL}/datasets/${selectedDataset}/tables/${selectedTable}`);
            return res.json();
        },
        enabled: !!selectedDataset && !!selectedTable
    })

    const { data: datasetStats, isLoading: statsLoading } = useQuery<DatasetStats>({
        queryKey: ['dataset-stats', selectedDataset],
        queryFn: async () => {
            if (!selectedDataset) return null;
            const statsRes = await fetch(`${API_URL}/datasets/${selectedDataset}/stats`);
            return statsRes.json();
        },
        enabled: !!selectedDataset
    })

    const queryMutation = useMutation({
        mutationFn: async () => {
            if (!selectedDataset || !query) {
                throw new Error('Dataset and query are required');
            }
            
            const res = await fetch(`${API_URL}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dataset_id: selectedDataset,
                    query: query
                }),
            })
            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail?.[0]?.msg || 'Query failed');
            }
            return res.json()
        },
        onError: (error) => {
            toast({
                title: 'Query Error',
                description: String(error),
                status: 'error',
                duration: 5000,
            })
        }
    })

    const insertFieldIntoQuery = useCallback((fieldName: string) => {
        const prefix = selectedDataset && selectedTable 
            ? `\`${selectedDataset}.${selectedTable}\`` 
            : '';
        // Check if this is the start of a new SELECT statement
        const isNewSelect = !query.toLowerCase().includes('select');
        
        // Check if we're adding to an existing field list
        const hasExistingFields = query.toLowerCase().includes('select') && 
            !query.toLowerCase().trim().endsWith('select');
        
        const newText = query.length > 0 
            ? isNewSelect
                ? `SELECT ${prefix}.${fieldName}`
                : hasExistingFields
                    ? `${query},\n  ${prefix}.${fieldName}`
                    : `${query} ${prefix}.${fieldName}`
            : `SELECT ${prefix}.${fieldName}`;
        
        setQuery(newText);
    }, [query, selectedDataset, selectedTable]);

    return (
        <ChakraGrid 
            templateColumns="300px 1fr" 
            h="100vh" 
            p={4} 
            gap={4} 
            bg={colorMode === 'dark' ? '#121212' : 'gray.50'}
        >
            {/* Color mode toggle */}
            <IconButton
                aria-label="Toggle color mode"
                icon={colorMode === 'dark' ? <SunIcon /> : <MoonIcon />}
                onClick={toggleColorMode}
                position="fixed"
                top={4}
                right={4}
                size="md"
                colorScheme="primary"
                variant="ghost"
                zIndex={1000}
                _hover={{
                    transform: 'rotate(45deg)',
                    bg: colorMode === 'dark' ? 'gray.800' : 'gray.100'
                }}
            />

            {/* Left sidebar */}
            <Card variant="glass">
                <CardHeader>
                    <Heading 
                        size="md" 
                        color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}
                    >
                        Datasets
                    </Heading>
                </CardHeader>
                <CardBody p={2}>
                    <Accordion allowMultiple>
                        {datasetsLoading ? (
                            <Spinner color="primary.500" />
                        ) : (
                            groupDatasets(datasets ?? []).map(group => (
                                <AccordionItem 
                                    key={group.category}
                                    border="none"
                                >
                                    <AccordionButton
                                        px={2}
                                        py={1}
                                        _hover={{
                                            bg: colorMode === 'dark' ? 'gray.700' : 'gray.100'
                                        }}
                                    >
                                        <Box flex="1">
                                            <Text 
                                                fontSize="sm" 
                                                fontWeight="bold" 
                                                color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}
                                            >
                                                {group.category.toUpperCase()}
                                            </Text>
                                        </Box>
                                        <Text 
                                            fontSize="xs" 
                                            color={colorMode === 'dark' ? 'gray.500' : 'gray.600'}
                                            mr={2}
                                        >
                                            {group.datasets.length} datasets
                                        </Text>
                                        <AccordionIcon />
                                    </AccordionButton>
                                    <AccordionPanel pb={2} px={1}>
                                        {group.datasets.map(dataset => (
                                            <Button
                                                key={dataset}
                                                variant="ghost"
                                                colorScheme="primary"
                                                onClick={() => setSelectedDataset(dataset)}
                                                onMouseEnter={() => prefetchTables(dataset)}
                                                justifyContent="flex-start"
                                                leftIcon={<StarIcon />}
                                                size="sm"
                                                py={4}
                                                maxW="100%"
                                                textAlign="left"
                                                height="auto"
                                                bg={selectedDataset === dataset ? 
                                                    (colorMode === 'dark' ? 'primary.900' : 'primary.50') 
                                                    : 'transparent'
                                                }
                                                fontWeight={selectedDataset === dataset ? 'semibold' : 'normal'}
                                                sx={{
                                                    '& > span': {
                                                        overflow: 'hidden',
                                                        textOverflow: 'ellipsis',
                                                        whiteSpace: 'nowrap',
                                                    }
                                                }}
                                                title={dataset}
                                            >
                                                {dataset}
                                            </Button>
                                        ))}
                                    </AccordionPanel>
                                </AccordionItem>
                            ))
                        )}
                    </Accordion>
                </CardBody>
            </Card>

            {/* Main content */}
            <VStack spacing={4} align="stretch" overflowY="auto" maxH="100vh">
                {selectedDataset && (
                    <>
                        <Card variant="glass">
                            <CardHeader>
                                <Heading 
                                    size="md" 
                                    color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}
                                >
                                    Tables in {selectedDataset}
                                </Heading>
                            </CardHeader>
                            <CardBody>
                                {tablesLoading ? (
                                    <Spinner color="primary.500" />
                                ) : (
                                    <Accordion allowMultiple>
                                        {groupTablesByDate(tables || []).map(group => (
                                            <AccordionItem 
                                                key={group.year}
                                                borderColor={colorMode === 'dark' ? 'gray.700' : 'gray.200'}
                                            >
                                                <AccordionButton>
                                                    <Box flex="1" textAlign="left">
                                                        <Text 
                                                            fontWeight="bold"
                                                            color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}
                                                        >
                                                            {group.year}
                                                        </Text>
                                                    </Box>
                                                    <AccordionIcon />
                                                </AccordionButton>
                                                <AccordionPanel>
                                                    <Accordion allowMultiple>
                                                        {Object.entries(group.months).map(([month, tables]) => (
                                                            <AccordionItem 
                                                                key={month}
                                                                borderColor={colorMode === 'dark' ? 'gray.700' : 'gray.200'}
                                                            >
                                                                <AccordionButton
                                                                    onClick={(e) => {
                                                                        e.preventDefault();
                                                                        setSelectedMonth({
                                                                            year: group.year,
                                                                            month,
                                                                            tables
                                                                        });
                                                                    }}
                                                                >
                                                                    <Box flex="1" textAlign="left">
                                                                        <Text color={colorMode === 'dark' ? 'gray.500' : 'gray.600'}>
                                                                            {getMonthName(month)}
                                                                        </Text>
                                                                    </Box>
                                                                    <HStack spacing={2}>
                                                                        <Text fontSize="sm" color={colorMode === 'dark' ? 'gray.500' : 'gray.600'}>
                                                                            {tables.length} tables
                                                                        </Text>
                                                                        <ChevronRightIcon />
                                                                    </HStack>
                                                                </AccordionButton>
                                                            </AccordionItem>
                                                        ))}
                                                    </Accordion>
                                                </AccordionPanel>
                                            </AccordionItem>
                                        ))}
                                    </Accordion>
                                )}
                            </CardBody>
                        </Card>

                        <Suspense fallback={<Spinner />}>
                            <QueryEditor
                                query={query}
                                setQuery={setQuery}
                                onRun={() => queryMutation.mutate()}
                                isLoading={queryMutation.isLoading}
                            />
                        </Suspense>

                        {(tableInfo || queryMutation.data) && (
                            <Suspense fallback={<Spinner />}>
                                <ResultsView
                                    tableInfo={tableInfo}
                                    queryResults={queryMutation.data}
                                    onFieldClick={insertFieldIntoQuery}
                                />
                            </Suspense>
                        )}

                        <Card variant="glass">
                            <CardBody>
                                <SimpleGrid columns={[1, 2, 4]} spacing={4}>
                                    {statsLoading ? (
                                        <Spinner color="primary.500" />
                                    ) : datasetStats && (
                                        <>
                                            <Box>
                                                <Text fontSize="sm" color={colorMode === 'dark' ? 'gray.400' : 'gray.600'}>
                                                    Tables
                                                </Text>
                                                <Text fontSize="2xl" fontWeight="bold" color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}>
                                                    {datasetStats.table_count}
                                                </Text>
                                            </Box>
                                            <Box>
                                                <Text fontSize="sm" color={colorMode === 'dark' ? 'gray.400' : 'gray.600'}>
                                                    Total Size
                                                </Text>
                                                <Text fontSize="2xl" fontWeight="bold" color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}>
                                                    {formatBytes(datasetStats.total_size_bytes)}
                                                </Text>
                                            </Box>
                                            <Box>
                                                <Text fontSize="sm" color={colorMode === 'dark' ? 'gray.400' : 'gray.600'}>
                                                    Last Modified
                                                </Text>
                                                <Text fontSize="lg" fontWeight="bold" color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}>
                                                    {(() => {
                                                        try {
                                                            return datasetStats.last_modified ? 
                                                                formatDistance(new Date(datasetStats.last_modified), new Date(), { addSuffix: true }) :
                                                                'Unknown';
                                                        } catch (e) {
                                                            return 'Unknown';
                                                        }
                                                    })()}
                                                </Text>
                                            </Box>
                                            {datasetStats.description && (
                                                <Box>
                                                    <Text fontSize="sm" color={colorMode === 'dark' ? 'gray.400' : 'gray.600'}>
                                                        Description
                                                    </Text>
                                                    <Text color={colorMode === 'dark' ? 'primary.200' : 'primary.700'}>
                                                        {datasetStats.description}
                                                    </Text>
                                                </Box>
                                            )}
                                        </>
                                    )}
                                </SimpleGrid>
                            </CardBody>
                        </Card>
                    </>
                )}
            </VStack>

            <Suspense fallback={null}>
                <TableSelector
                    isOpen={!!selectedMonth}
                    onClose={() => setSelectedMonth(undefined)}
                    tables={selectedMonth?.tables || []}
                    onSelect={setSelectedTable}
                    selectedTable={selectedTable}
                    title={selectedMonth ? `Tables from ${getMonthName(selectedMonth.month)} ${selectedMonth.year}` : ''}
                />
            </Suspense>
        </ChakraGrid>
    )
} 