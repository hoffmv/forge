import { useEffect, useRef, useState, useCallback } from 'react'

export default function useWebSocket(project, apiBase) {
  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const clearEvents = useCallback(() => setEvents([]), [])

  useEffect(() => {
    if (!project) {
      setConnected(false)
      return
    }

    const wsBase = apiBase.replace(/^http/, 'ws')
    const url = `${wsBase}/agent/events/${project}`
    let shouldReconnect = true

    function connect() {
      if (wsRef.current) {
        wsRef.current.close()
      }

      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        if (reconnectTimer.current) {
          clearTimeout(reconnectTimer.current)
          reconnectTimer.current = null
        }
      }

      ws.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data)
          setEvents(prev => [...prev, event])
        } catch (e) {
          // ignore malformed messages
        }
      }

      ws.onclose = () => {
        setConnected(false)
        wsRef.current = null
        if (shouldReconnect) {
          reconnectTimer.current = setTimeout(connect, 3000)
        }
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      shouldReconnect = false
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [project, apiBase])

  return { events, connected, clearEvents }
}
