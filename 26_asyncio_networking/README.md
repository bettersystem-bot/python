# 26 asyncio 网络编程

## 这一章学什么

前面已经学过 `asyncio` 和 TCP 流式 I/O，这一章把它们正式放到“网络编程”语境里。

你会学到：

- `asyncio.start_server()` 如何创建异步 TCP 服务端
- `asyncio.open_connection()` 如何创建异步客户端
- `StreamReader` / `StreamWriter` 的职责
- 如何同时启动多个异步客户端

## 和 selectors 的关系

你可以把 `asyncio` 理解成更高级的事件循环框架。

底层会利用操作系统的 I/O 多路复用能力，上层给你 `async` / `await` 这种更友好的写法。

## 运行方式

```bash
python3.10 26_asyncio_networking/asyncio_tcp_chat.py
```
