import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChakraProvider, ColorModeScript } from '@chakra-ui/react'
import Explorer from './components/Explorer'
import { theme } from './theme'

const queryClient = new QueryClient()

function App() {
    return (
        <>
            <ColorModeScript initialColorMode={theme.config.initialColorMode} />
            <QueryClientProvider client={queryClient}>
                <ChakraProvider theme={theme}>
                    <Explorer />
                </ChakraProvider>
            </QueryClientProvider>
        </>
    )
}

export default App