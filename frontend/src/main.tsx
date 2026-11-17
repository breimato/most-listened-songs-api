import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'
import { AccessGate } from './components/AccessGate'
import './index.css'
import {
  clearStoredAccessKey,
  persistAccessKey,
  readStoredAccessKey,
  setAccessKey,
  subscribeUnauthorized,
} from './services/auth'
import { loadRuntimeConfig } from './services/runtimeConfig'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
    },
  },
})

function Root() {
  const [key, setKey] = useState(() => {
    const stored = readStoredAccessKey()
    setAccessKey(stored)
    return stored
  })

  useEffect(
    () =>
      subscribeUnauthorized(() => {
        setKey('')
      }),
    [],
  )

  if (!key) {
    return (
      <AccessGate
        onUnlock={(value, remember) => {
          persistAccessKey(value, remember)
          setKey(value)
        }}
      />
    )
  }

  return (
    <QueryClientProvider client={queryClient}>
      <App
        onLock={() => {
          clearStoredAccessKey()
          setKey('')
        }}
      />
    </QueryClientProvider>
  )
}

loadRuntimeConfig().finally(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <Root />
    </StrictMode>,
  )
})
