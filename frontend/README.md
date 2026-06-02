# Frontend —— React 实时编排控制台

基于 **React 18 + Vite**，零重型依赖，DAG 图用原生 SVG 绘制。

## 功能

- 选择内置示例 DAG，一键提交到后端。
- 通过 WebSocket 订阅 `/ws/events`，**实时**刷新 DAG 图上每个节点的状态颜色。
- 左侧滚动显示事件流（node_dispatched / running / succeeded / failed / retry / skipped …）。
- 右侧实时展示后端指标（派发数、成功/失败数、节点耗时 p50/p95、各 worker 在途数）。

## 本地开发

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

开发服务器会把 `/api`、`/ws` 代理到 `http://localhost:8000`（见 vite.config.js）。
若后端不在该地址，用 `VITE_BACKEND=http://host:port npm run dev` 覆盖。

## 目录

```
src/
├── main.jsx            # 入口
├── App.jsx             # 主界面：提交 / 事件流 / 指标
├── DagGraph.jsx        # SVG 绘制的 DAG 图（按拓扑分层布局）
├── api.js              # 后端 REST 封装
├── useEventStream.js   # WebSocket 事件订阅 hook（自动重连）
└── styles.css
```
