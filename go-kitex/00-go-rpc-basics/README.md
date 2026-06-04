# 00 RPC 基础：为什么需要 Kitex

## 学习目标

- 区分本地函数调用和远程过程调用（RPC）。
- 理解 Client、Server、Request、Response 的关系。
- 理解 IDL 为什么是微服务之间的接口契约。

## 本地调用 vs RPC 调用

本地函数调用只发生在同一个进程内：

```go
message := Echo("hello")
```

RPC 让调用方看起来像在调用本地函数，但真实过程跨越网络：

```text
Client 构造 Request
  ↓
序列化为网络数据
  ↓
发送到 Server
  ↓
Server 反序列化并执行 Handler
  ↓
Server 返回 Response
  ↓
Client 反序列化并得到结果
```

Kitex 负责把网络通信、序列化、连接管理、Client/Server 框架代码等重复工作封装起来，让业务开发者聚焦接口契约和业务逻辑。

## IDL 的作用

IDL（Interface Definition Language）用于定义：

- 请求结构体：Client 要传什么。
- 响应结构体：Server 会返回什么。
- 服务方法：有哪些 RPC 方法、方法参数是什么。

Kitex 根据 IDL 生成 Go 代码，所以 IDL 是调用方和服务方共同遵守的契约。

## 先记住这条链路

```text
echo.thrift
  ↓ kitex 代码生成
kitex_gen/echo/...
  ↓ Server 实现 Handler
EchoServiceImpl.Echo(ctx, req)
  ↓ Client 调用
cli.Echo(ctx, req)
```

后面的章节都会围绕这条链路展开。
