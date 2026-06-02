import { useEffect, useRef, useState } from 'react'

// 订阅后端 WebSocket 事件流（/ws/events）。
// 返回最近的事件列表与连接状态；断线自动重连。
export function useEventStream(onEvent) {
  const [connected, setConnected] = useState(false)
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    let ws
    let stopped = false
    let retry

    function connect() {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${proto}://${location.host}/ws/events`)
      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        if (!stopped) retry = setTimeout(connect, 1500) // 自动重连
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data)
          onEventRef.current?.(event)
        } catch (_) { /* ignore */ }
      }
    }
    connect()
    return () => {
      stopped = true
      clearTimeout(retry)
      ws && ws.close()
    }
  }, [])

  return { connected }
}
