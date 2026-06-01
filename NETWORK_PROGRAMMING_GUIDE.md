# Python 网络编程学习总览

这个专题聚焦 Python 网络编程，从最底层的 socket 开始，一步步走到 HTTP、并发服务端、非阻塞 I/O 和 asyncio 网络编程。

## 学习目标

学完以后，你应该能回答这些问题：

- TCP 和 UDP 有什么区别？
- socket 编程里的 bind、listen、accept、connect 分别做什么？
- 为什么 TCP 会有粘包和拆包问题？
- 网络程序为什么必须设置 timeout？
- HTTP 请求和响应本质上是什么？
- 如何写一个并发处理多个客户端的服务端？
- 阻塞、非阻塞、select、asyncio 之间是什么关系？

## 学习顺序

1. `19_network_overview`：网络编程基本概念、IP、端口、协议、字节流
2. `20_tcp_socket`：用原生 socket 写 TCP echo server/client
3. `21_udp_socket`：用 UDP 理解无连接通信
4. `22_http_basics`：用标准库理解 HTTP 请求、响应和本地 HTTP 服务
5. `23_framing_timeouts`：讲清楚 TCP 粘包/拆包、消息边界和 timeout
6. `24_concurrent_servers`：用线程和 `socketserver` 写并发 TCP 服务端
7. `25_selectors_nonblocking`：用 `selectors` 理解非阻塞 I/O 和事件驱动
8. `26_asyncio_networking`：用 `asyncio` 写异步 TCP server/client

## 一个形象模型

你可以把网络编程想象成寄快递：

- IP 地址：收件人所在城市和小区
- 端口：收件人家的门牌号
- TCP：签收制快递，可靠、有顺序、会确认
- UDP：明信片，轻量、快，但不保证一定到
- socket：你手里的电话或快递窗口
- HTTP：双方约定好的对话格式
- timeout：你不可能永远站在门口等对方回应

## 最重要的工程原则

- 网络里传输的是字节，不是 Python 对象
- TCP 是字节流，不天然保留消息边界
- 所有网络调用都可能失败
- 所有网络等待都应该考虑 timeout
- 服务端必须考虑多个客户端同时连接
- 协议设计要明确：长度、分隔符、编码、错误处理
- 先用本机 `127.0.0.1` 练习，再连接真实网络

## 运行说明

所有示例都尽量使用本机端口，并让操作系统自动分配空闲端口，避免端口冲突。

推荐使用 Python 3.10：

```bash
python3.10 20_tcp_socket/tcp_echo_demo.py
```
