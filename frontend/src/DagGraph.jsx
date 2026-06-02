import React, { useMemo } from 'react'

// 节点状态对应的颜色。
const STATUS_COLOR = {
  pending: '#9aa7b8',
  ready: '#f0ad4e',
  dispatched: '#5bc0de',
  running: '#4a90e2',
  succeeded: '#5cb85c',
  failed: '#d9534f',
  skipped: '#b0b0b0',
}

const STATUS_LABEL = {
  pending: '待依赖', ready: '就绪', dispatched: '已派发', running: '执行中',
  succeeded: '成功', failed: '失败', skipped: '跳过',
}

// 按拓扑层级给节点分层（每个节点的层 = 其所有上游层的最大值 + 1）。
function computeLayers(nodes) {
  const byId = {}
  Object.values(nodes).forEach((n) => { byId[n.id] = n })
  const level = {}
  function depth(id, seen = new Set()) {
    if (level[id] != null) return level[id]
    if (seen.has(id)) return 0
    seen.add(id)
    const n = byId[id]
    if (!n || n.depends_on.length === 0) { level[id] = 0; return 0 }
    const d = 1 + Math.max(...n.depends_on.map((p) => depth(p, seen)))
    level[id] = d
    return d
  }
  Object.keys(byId).forEach((id) => depth(id))
  return level
}

export default function DagGraph({ run }) {
  const layout = useMemo(() => {
    if (!run || !run.nodes) return null
    const nodes = run.nodes
    const level = computeLayers(nodes)
    const cols = {}
    Object.values(nodes).forEach((n) => {
      const l = level[n.id]
      cols[l] = cols[l] || []
      cols[l].push(n)
    })
    const colW = 200, rowH = 92, padX = 40, padY = 40
    const pos = {}
    Object.keys(cols).forEach((l) => {
      cols[l].forEach((n, i) => {
        pos[n.id] = { x: padX + l * colW, y: padY + i * rowH }
      })
    })
    const maxRows = Math.max(...Object.values(cols).map((c) => c.length), 1)
    const maxCol = Math.max(...Object.keys(cols).map(Number), 0)
    return {
      pos,
      width: padX * 2 + (maxCol + 1) * colW,
      height: padY * 2 + maxRows * rowH,
    }
  }, [run])

  if (!run || !layout) {
    return <div className="empty">提交一张 DAG 后，这里会实时显示编排执行过程</div>
  }

  const nodes = Object.values(run.nodes)
  const NW = 150, NH = 56

  return (
    <svg className="dag-svg" width={layout.width} height={layout.height}>
      {/* 依赖边 */}
      {nodes.map((n) =>
        n.depends_on.map((dep) => {
          const a = layout.pos[dep], b = layout.pos[n.id]
          if (!a || !b) return null
          const x1 = a.x + NW, y1 = a.y + NH / 2
          const x2 = b.x, y2 = b.y + NH / 2
          const mx = (x1 + x2) / 2
          return (
            <path key={`${dep}-${n.id}`} className="edge"
              d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`} />
          )
        })
      )}
      {/* 节点 */}
      {nodes.map((n) => {
        const p = layout.pos[n.id]
        const color = STATUS_COLOR[n.status] || '#999'
        return (
          <g key={n.id} transform={`translate(${p.x},${p.y})`}>
            <rect width={NW} height={NH} rx="8" fill="#fff" stroke={color} strokeWidth="2.5" />
            <rect width="6" height={NH} rx="3" fill={color} />
            <text x="16" y="22" className="node-name">{n.name}</text>
            <text x="16" y="42" className="node-meta">
              {n.type.toUpperCase()} · {STATUS_LABEL[n.status] || n.status}
            </text>
            {n.status === 'running' && (
              <circle cx={NW - 16} cy="16" r="5" className="pulse" fill={color} />
            )}
          </g>
        )
      })}
    </svg>
  )
}

export { STATUS_COLOR, STATUS_LABEL }
