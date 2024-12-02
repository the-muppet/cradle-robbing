import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChakraProvider, ColorModeScript, extendTheme } from '@chakra-ui/react'
import Explorer from './components/Explorer'

const theme = extendTheme({
    config: {
        initialColorMode: 'dark',
        useSystemColorMode: true,
    },
    colors: {
        primary: {
            50: '#e8eaf6',
            100: '#c5cae9',
            200: '#9fa8da',
            300: '#7986cb',
            400: '#5c6bc0',
            500: '#3f51b5',
            600: '#3949ab',
            700: '#303f9f',
            800: '#283593',
            900: '#1a237e',
        }
    },
    styles: {
        global: (props: any) => ({
            body: {
                bg: props.colorMode === 'dark' ? '#121212' : 'gray.50',
                backgroundImage: props.colorMode === 'dark'
                    ? 'radial-gradient(circle at 50% 50%, rgba(63, 81, 181, 0.03) 0%, transparent 100%)'
                    : 'radial-gradient(circle at 50% 50%, rgba(63, 81, 181, 0.02) 0%, transparent 100%)',
                '@keyframes gradient': {
                    '0%': { backgroundPosition: '0% 50%' },
                    '50%': { backgroundPosition: '100% 50%' },
                    '100%': { backgroundPosition: '0% 50%' }
                },
                animation: 'gradient 15s ease infinite',
                backgroundSize: '200% 200%'
            },
        })
    },
    components: {
        Card: {
            variants: {
                glass: (props: any) => ({
                    container: {
                        backgroundColor: props.colorMode === 'dark'
                            ? 'rgba(30, 30, 30, 0.8)'
                            : 'rgba(255, 255, 255, 0.85)',
                        backgroundImage: props.colorMode === 'dark'
                            ? 'linear-gradient(180deg, rgba(63, 81, 181, 0.05) 0%, rgba(30, 30, 30, 0) 100%)'
                            : 'linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%)',
                        backdropFilter: 'blur(10px)',
                        borderWidth: '1px',
                        borderColor: props.colorMode === 'dark'
                            ? 'gray.700'
                            : 'gray.200',
                        boxShadow: props.colorMode === 'dark'
                            ? '0 4px 30px rgba(0, 0, 0, 0.1)'
                            : '0 4px 30px rgba(0, 0, 0, 0.05)',
                    }
                })
            }
        },
        Button: {
            variants: {
                ghost: (props: any) => ({
                    _hover: {
                        bg: props.colorMode === 'dark' ? 'gray.800' : 'gray.100',
                        color: props.colorMode === 'dark' ? 'primary.300' : 'primary.500'
                    }
                })
            }
        },
        AccordionItem: {
            baseStyle: {
                borderTopWidth: '0px',
                '& > button': {
                    '& > *': {
                    }
                },
                '& > div': {
                    overflow: 'hidden'
                }
            }
        },
        AccordionButton: {
            baseStyle: (props: any) => ({
                '& svg': {
                    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                },
                '&[aria-expanded=true] svg': {
                    transform: 'rotate(-180deg)'
                },
                _hover: {
                    bg: props.colorMode === 'dark' ? 'gray.800' : 'gray.100'
                }
            })
        }
    }
})

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