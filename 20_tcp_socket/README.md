# 20 TCP Socket 基础

## 这一章学什么

这一章用原生 `socket` 写一个 TCP echo server/client。

你会学到：

- 服务端 `socket()`、`bind()`、`listen()`、`accept()` 的顺序
- 客户端 `connect()` 的作用
- `sendall()` 和 `recv()` 如何收发字节
- 为什么网络传输要自己处理编码和解码

## TCP 服务端流程

1. 创建 socket
2. 绑定 IP 和端口
3. 开始监听
4. 接受客户端连接
5. 收发数据
6. 关闭连接

## TCP 客户端流程

1. 创建 socket
2. 连接服务端
3. 发送数据
4. 接收响应
5. 关闭连接

## 运行方式

```bash
python3.10 20_tcp_socket/tcp_echo_demo.py
```

这个示例会在一个后台线程里启动服务端，然后客户端连接它，最后自动退出。
