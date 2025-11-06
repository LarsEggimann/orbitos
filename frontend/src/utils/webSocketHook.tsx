import { useEffect, useRef, useState } from 'react'
import type { BaseWebSocketMessage } from '~/generated'
import { useRouterState } from '@tanstack/react-router'

interface UseDeviceWebSocketOptions<TState, TData, TSettings> {
  url: string
  fetchInitialState: () => Promise<TState>
  fetchInitialSettings: () => Promise<TSettings>
  dataAppendFunction: (newData: TData) => void
}

export function useDeviceWebSocket<TState, TData, TSettings>({
  url,
  fetchInitialState,
  fetchInitialSettings,
  dataAppendFunction,
}: UseDeviceWebSocketOptions<TState, TData, TSettings>) {
  const wsRef = useRef<WebSocket | null>(null)
  const [state, setState] = useState<TState | null>(null)
  const [settings, setSettings] = useState<TSettings | null>(null)
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const { status } = useRouterState() // status: 'pending' | 'idle' | ...

  useEffect(() => {
    if (status !== 'idle') return // Only connect when router is ready
    let reconnectTimeout: NodeJS.Timeout
    let isUnmounting = false

    const connectWebSocket = () => {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        console.log('WebSocket connected:', url)
      }

      ws.onclose = () => {
        setConnected(false)
        if (!isUnmounting) {
          console.warn('WebSocket closed unexpectedly -> Reconnecting...')
          reconnectTimeout = setTimeout(connectWebSocket, 2000)
        }
        console.log('WebSocket closed:', url)
      }

      ws.onerror = (err) => {
        console.error('WebSocket error', err)
        ws.close()
      }

      ws.onmessage = (event) => {
        try {
          const message: BaseWebSocketMessage = JSON.parse(event.data)

          switch (message.type) {
            case 'state':
              setState(message.content as TState)
              break
            case 'data':
              dataAppendFunction(message.content as TData)
              break
            case 'settings':
              setSettings(message.content as TSettings)
              break
            default:
              console.warn('Unknown message type:', message.type)
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message', err)
        }
      }
    }
    connectWebSocket()

    return () => {
      isUnmounting = true
      clearTimeout(reconnectTimeout)
      wsRef.current?.close()
    }
  }, [url, status])

  useEffect(() => {
    let cancelled = false

    const loadInitial = async () => {
      try {
        // when switching devices (url changes), reset to loading state
        setLoading(true)
        setError(null)
        // clear stale values while loading the new device
        setState(null)
        setSettings(null)

        const [s, set] = await Promise.all([
          fetchInitialState(),
          fetchInitialSettings(),
        ])
        if (!cancelled) {
          setState(s)
          setSettings(set)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadInitial()

    return () => {
      cancelled = true
    }
    // Re-load initial state/settings whenever the device URL changes
  }, [url])

  return { state, settings, connected, loading, error }
}
