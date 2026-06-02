// 后端 API 封装。开发环境通过 Vite 代理到 :8000，生产环境同源。

export async function listExamples() {
  const r = await fetch('/api/examples')
  if (!r.ok) throw new Error('加载示例失败')
  return r.json()
}

export async function submitDag(spec) {
  const r = await fetch('/api/dags', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(spec),
  })
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}))
    throw new Error(detail.detail || '提交失败')
  }
  return r.json()
}

export async function getDag(id) {
  const r = await fetch(`/api/dags/${id}`)
  if (!r.ok) throw new Error('查询失败')
  return r.json()
}

export async function listDags() {
  const r = await fetch('/api/dags')
  if (!r.ok) throw new Error('查询失败')
  return r.json()
}

export async function getMetrics() {
  const r = await fetch('/api/metrics')
  if (!r.ok) throw new Error('查询指标失败')
  return r.json()
}
