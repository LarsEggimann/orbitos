import { useEffect, useRef, useState } from 'react'
import { BaseWebSocketMessage } from '~/generated'

interface UseDeviceWebSocketOptions<TState, TData, TSettings> {
  url: string
  fetchInitialState: () => Promise<TState>
  fetchInitialData: () => Promise<TData>
  fetchInitialSettings: () => Promise<TSettings>
}

export function useDeviceWebSocket<TState, TData, TSettings>({
  url,
  fetchInitialState,
  fetchInitialData,
  fetchInitialSettings,
}: UseDeviceWebSocketOptions<TState, TData, TSettings>) {
  const wsRef = useRef<WebSocket | null>(null)
  const [state, setState] = useState<TState | null>(null)
  const [data, setData] = useState<TData | null>(null)
  const [settings, setSettings] = useState<TSettings | null>(null)
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)


  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout

    const connectWebSocket = () => {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        console.log('WebSocket connected:', url)
      }

      ws.onclose = () => {
        console.warn('WebSocket closed. Reconnecting...')
        setConnected(false)
        reconnectTimeout = setTimeout(connectWebSocket, 2000)
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
              setData(message.content as TData)
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
      clearTimeout(reconnectTimeout)
      wsRef.current?.close()
    }
  }, [url])


  useEffect(() => {
    let cancelled = false

    const loadInitial = async () => {
      try {
        setLoading(true)
        const [s, d, set] = await Promise.all([
          fetchInitialState(),
          fetchInitialData(),
          fetchInitialSettings(),
        ])
        if (!cancelled) {
          setState(s)
          setData(d)
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
  }, [])

  return { state, data, settings, connected, loading, error }
}
