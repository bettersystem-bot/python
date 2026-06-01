# 24 并发 TCP 服务端

## 这一章学什么

一个服务端如果一次只能处理一个客户端，就很难用于真实场景。

这一章会演示两种并发服务端思路：

- 手动为每个连接创建线程
- 使用标准库 `socketserver.ThreadingTCPServer`

这里重点展示 `socketserver`，因为它能帮你少写很多重复代码。

## 为什么服务端需要并发

如果客户端 A 连接后迟迟不发数据，单线程阻塞服务端可能就没法处理客户端 B。

并发服务端可以让多个连接同时推进。

## 运行方式

```bash
python3.10 24_concurrent_servers/threading_tcp_server.py
```
