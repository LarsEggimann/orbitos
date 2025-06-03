import { useEffect, useRef, useState } from 'react'
import { BaseWebSocketMessage, ElectrometerState, CurrentDataResponse, ElectrometerSettings } from '~/generated'

interface UseWebSocketOptions {
  url: string
}

export function useWebSocket({ url }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const [state, setState] = useState<ElectrometerState | null>(null)
  const [data, setData] = useState<CurrentDataResponse | null>(null)
  const [settings, setSettings] = useState<ElectrometerSettings | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout

    const connect = () => {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        console.log('WebSocket connected:', url)
      }

      ws.onclose = () => {
        console.warn('WebSocket closed. Reconnecting...')
        setConnected(false)
        reconnectTimeout = setTimeout(connect, 2000)
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
              setState(message.content as ElectrometerState)
              break
            case 'data':
              setData(message.content as CurrentDataResponse)
              break
            case 'settings':
              setSettings(message.content as ElectrometerSettings)
              break
            default:
              console.warn('Unknown message type:', message.type)
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message', err)
        }
      }
    }

    connect()

    return () => {
      clearTimeout(reconnectTimeout)
      wsRef.current?.close()
    }
  }, [url])

  return { state, data, settings, connected }
}
