import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { DefaultCatchBoundary } from './components/DefaultCatchBoundary'
import { NotFound } from './components/NotFound'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { ThemeProvider } from '~/provider/ThemeProvider'
import { ConfigProvider, useConfig } from '~/provider/ConfigProvider'
import { client } from '~/generated/client.gen'

// Import the generated route tree
import { routeTree } from './routeTree.gen'

// Create a new router instance
const router = createRouter({
  routeTree,
  context: {},
  defaultPreload: 'intent',
  scrollRestoration: true,
  defaultStructuralSharing: true,
  defaultPreloadStaleTime: 0,
  defaultErrorComponent: DefaultCatchBoundary,
  defaultNotFoundComponent: () => <NotFound />,
})

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

const queryClient = new QueryClient()

function AppProviders({ children }: { readonly children: React.ReactNode }) {
  const { API_BASE_URL } = useConfig();
  // Set the client baseURL dynamically
  client.setConfig({ baseURL: API_BASE_URL });
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
}

// Render the app
const rootElement = document.getElementById('app')
if (rootElement && !rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <StrictMode>
      <ConfigProvider>
        <AppProviders>
          {/* Provide the router to the app */}
          <RouterProvider router={router} />
        </AppProviders>
      </ConfigProvider>
    </StrictMode>,
  )
}
