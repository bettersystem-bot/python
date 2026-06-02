import React, { useEffect, useState, useCallback } from 'react'
import { listExamples, submitDag, getDag, getMetrics } from './api'
import { useEventStream } from './useEventStream'
import DagGraph, { STATUS_COLOR, STATUS_LABEL } from './DagGraph'

export default function App() {
  const [examples, setExamples] = useState({})
  const [selected, setSelected] = useState('diamond')
  const [run, setRun] = useState(null)        // 当前正在观察的 DagRun 完整状态
  const [events, setEvents] = useState([])     // 事件日志（最近 N 条）
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState('')
  const [activeId, setActiveId] = useState(null)

  // 加载示例 DAG 列表。
  useEffect(() => { listExamples().then(setExamples).catch((e) => setError(e.message)) }, [])

  // 收到事件：记录日志；若与当前观察的 DAG 相关，则重新拉取该 DAG 的完整状态来刷新图。
  const onEvent = useCallback((ev) => {
    setEvents((prev) => [ev, ...prev].slice(0, 200))
    setActiveId((curId) => {
      if (ev.dag_run_id && ev.dag_run_id === curId) {
        getDag(curId).then(setRun).catch(() => {})
      }
      return curId
    })
  }, [])
  const { connected } = useEventStream(onEvent)

  // 定时刷新指标。
  useEffect(() => {
    const t = setInterval(() => getMetrics().then(setMetrics).catch(() => {}), 1500)
    return () => clearInterval(t)
  }, [])

  async function handleSubmit() {
    setError('')
    const spec = examples[selected]
    if (!spec) return
    try {
      const res = await submitDag(spec)
      setActiveId(res.dag_run_id)
      setEvents([])
      const full = await getDag(res.dag_run_id)
      setRun(full)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">异步编排调度控制台</div>
        <div className={`conn ${connected ? 'on' : 'off'}`}>
          <span className="dot" /> WebSocket {connected ? '已连接' : '断开'}
        </div>
      </header>

      <div className="layout">
        {/* 左侧：控制 + 事件日志 */}
        <aside className="sidebar">
          <section className="panel">
            <h3>1. 选择示例 DAG</h3>
            <select value={selected} onChange={(e) => setSelected(e.target.value)}>
              {Object.entries(examples).map(([k, v]) => (
                <option key={k} value={k}>{v.name}</option>
              ))}
            </select>
            {examples[selected] && (
              <div className="hint">
                节点数：{examples[selected].nodes.length} ·
                失败策略：{examples[selected].failure_policy}
              </div>
            )}
            <button className="primary" onClick={handleSubmit}>提交并实时观察</button>
            {error && <div className="error">{error}</div>}
          </section>

          <section className="panel grow">
            <h3>事件流（EventBus → WebSocket）</h3>
            <div className="events">
              {events.length === 0 && <div className="muted">等待事件…</div>}
              {events.map((ev, i) => (
                <div className="event" key={i}>
                  <span className="evt-type" style={{ color: evColor(ev.type) }}>{ev.type}</span>
                  {ev.node_id && <span className="evt-node">{ev.node_id}</span>}
                  <span className="evt-ts">{fmtTs(ev.ts)}</span>
                </div>
              ))}
            </div>
          </section>
        </aside>

        {/* 中间：DAG 图 */}
        <main className="canvas">
          <div className="canvas-head">
            <h3>编排执行视图 {run && <span className="run-id">#{run.id}</span>}</h3>
            {run && <StatusBadges run={run} />}
          </div>
          <div className="graph-wrap">
            <DagGraph run={run} />
          </div>
          <Legend />
        </main>

        {/* 右侧：指标 */}
        <aside className="metrics-pane">
          <section className="panel">
            <h3>指标 metrics</h3>
            <MetricsView metrics={metrics} />
          </section>
        </aside>
      </div>
    </div>
  )
}

function StatusBadges({ run }) {
  const counts = {}
  Object.values(run.nodes).forEach((n) => { counts[n.status] = (counts[n.status] || 0) + 1 })
  return (
    <div className="badges">
      <span className={`dag-status ${run.status}`}>{run.status}</span>
      {Object.entries(counts).map(([s, c]) => (
        <span className="badge" key={s} style={{ borderColor: STATUS_COLOR[s] }}>
          <i style={{ background: STATUS_COLOR[s] }} />{STATUS_LABEL[s] || s} {c}
        </span>
      ))}
    </div>
  )
}

function Legend() {
  return (
    <div className="legend">
      {Object.entries(STATUS_LABEL).map(([k, label]) => (
        <span key={k} className="legend-item">
          <i style={{ background: STATUS_COLOR[k] }} />{label}
        </span>
      ))}
    </div>
  )
}

function MetricsView({ metrics }) {
  if (!metrics) return <div className="muted">加载中…</div>
  const { counters = {}, gauges = {}, timings = {} } = metrics
  return (
    <div className="metrics">
      <h4>计数器</h4>
      {Object.entries(counters).sort().map(([k, v]) => (
        <div className="mrow" key={k}><span>{k}</span><b>{v}</b></div>
      ))}
      <h4>瞬时值</h4>
      {Object.entries(gauges).sort().map(([k, v]) => (
        <div className="mrow" key={k}><span>{k}</span><b>{v}</b></div>
      ))}
      <h4>耗时(ms)</h4>
      {Object.entries(timings).map(([k, v]) => (
        <div className="mrow" key={k}><span>{k}</span><b>p50={v.p50} p95={v.p95}</b></div>
      ))}
    </div>
  )
}

function evColor(type) {
  if (type.includes('failed')) return '#d9534f'
  if (type.includes('succeeded') || type.includes('finished')) return '#5cb85c'
  if (type.includes('running') || type.includes('dispatched')) return '#4a90e2'
  if (type.includes('retry') || type.includes('skipped')) return '#f0ad4e'
  return '#888'
}

function fmtTs(ts) {
  const d = new Date(ts * 1000)
  return d.toLocaleTimeString('zh-CN', { hour12: false }) + '.' + String(d.getMilliseconds()).padStart(3, '0')
}
