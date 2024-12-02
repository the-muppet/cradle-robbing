import {
    Card,
    CardHeader,
    CardBody,
    Heading,
    VStack,
    Textarea,
    HStack,
    Button,
    useColorMode,
    Kbd,
    Text,
    Tooltip,
} from '@chakra-ui/react'
import { ChevronRightIcon, ChevronDownIcon } from '@chakra-ui/icons'
import { useCallback } from 'react'

interface QueryEditorProps {
    query: string;
    setQuery: (query: string) => void;
    onRun: () => void;
    isLoading: boolean;
}

export default function QueryEditor({ query, setQuery, onRun, isLoading }: QueryEditorProps) {
    const { colorMode } = useColorMode()
    
    const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            onRun();
        }
    }, [onRun]);
    
    return (
        <Card variant="glass">
            <CardHeader>
                <HStack justify="space-between">
                    <Heading size="md">Query Editor</Heading>
                    <HStack spacing={2}>
                        <Kbd size="sm">ctrl</Kbd>
                        <Text>+</Text>
                        <Kbd size="sm">enter</Kbd>
                        <Text fontSize="sm">to run</Text>
                    </HStack>
                </HStack>
            </CardHeader>
            <CardBody>
                <VStack spacing={4} align="stretch">
                    <Textarea
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Enter your SQL query..."
                        size="sm"
                        fontFamily="monospace"
                        minH="100px"
                        bg={colorMode === 'dark' ? 'rgba(30, 30, 30, 0.8)' : 'rgba(255, 255, 255, 0.85)'}
                        borderColor={colorMode === 'dark' ? 'gray.700' : 'gray.200'}
                        _focus={{
                            borderColor: colorMode === 'dark' ? 'primary.500' : 'primary.400',
                            boxShadow: `0 0 0 1px ${colorMode === 'dark' ? 'primary.500' : 'primary.400'}`
                        }}
                        onKeyDown={handleKeyPress}
                    />
                    <HStack>
                        <Tooltip label="Run query (Ctrl+Enter)" placement="top">
                            <Button
                                leftIcon={<ChevronRightIcon />}
                                colorScheme="primary"
                                onClick={onRun}
                                isLoading={isLoading}
                                size="sm"
                            >
                                Run Query
                            </Button>
                        </Tooltip>
                        <Tooltip label="Download results as CSV" placement="top">
                            <Button
                                leftIcon={<ChevronDownIcon />}
                                variant="outline"
                                colorScheme="primary"
                                size="sm"
                            >
                                Export Results
                            </Button>
                        </Tooltip>
                    </HStack>
                </VStack>
            </CardBody>
        </Card>
    )
} 