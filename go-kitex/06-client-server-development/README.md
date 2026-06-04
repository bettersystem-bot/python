# 06 Client / Server 开发实践

## 学习目标

- 知道业务逻辑写在 Handler。
- 学会创建本地直连 Client。
- 区分业务错误和 RPC 框架错误。
- 使用中间件放置横切逻辑。

## Handler 只做业务逻辑

```go
func (s *EchoServiceImpl) Echo(
    ctx context.Context,
    req *echo.EchoRequest,
) (*echo.EchoResponse, error) {
    if req == nil || req.Message == "" {
        return nil, fmt.Errorf("message is required")
    }

    return &echo.EchoResponse{Message: "server received: " + req.Message}, nil
}
```

真实业务里可以把参数校验、领域逻辑、仓储访问拆到独立包中，Handler 保持薄入口。

## Client 创建和调用

```go
cli, err := echoservice.NewClient(
    "echo.service",
    client.WithHostPorts("127.0.0.1:8888"),
    client.WithRPCTimeout(200*time.Millisecond),
)
if err != nil {
    return err
}

resp, err := cli.Echo(ctx, &echo.EchoRequest{Message: "hello"})
```

教学示例使用 `WithHostPorts`；线上服务更常见的是通过服务发现找到实例。

## 动态超时

```go
ctx, cancel := context.WithTimeout(context.Background(), 300*time.Millisecond)
defer cancel()

resp, err := cli.Echo(
    ctx,
    req,
    callopt.WithRPCTimeout(200*time.Millisecond),
)
```

理解两点：

- `context` 可以传递取消和 deadline。
- 单次调用的 call option 适合覆盖默认超时。

## 错误处理思路

先区分两类错误：

1. RPC 框架错误：超时、连接失败、服务不可用、序列化失败等。
2. 业务错误：参数不合法、资源不存在、业务状态不允许等。

示例：

```go
resp, err := cli.Echo(ctx, req)
if err != nil {
    if kerrors.IsTimeoutError(err) {
        log.Printf("rpc timeout request_id=%s err=%v", req.RequestId, err)
        return err
    }
    log.Printf("rpc failed request_id=%s err=%v", req.RequestId, err)
    return err
}

log.Printf("response=%s", resp.Message)
```

不要只打印 `err`。至少带上关键请求字段、方法名、耗时、trace / request id。

## 中间件：统一横切逻辑

```go
func LogMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        start := time.Now()
        err := next(ctx, req, resp)
        log.Printf("rpc cost=%s err=%v", time.Since(start), err)
        return err
    }
}
```

Client 注册：

```go
cli, err := echoservice.NewClient(
    "echo.service",
    client.WithHostPorts("127.0.0.1:8888"),
    client.WithMiddleware(LogMiddleware),
)
```

Server 注册：

```go
svr := echoservice.NewServer(
    new(EchoServiceImpl),
    server.WithServiceAddr(addr),
    server.WithMiddleware(LogMiddleware),
)
```

中间件适合日志、监控、追踪、鉴权、参数校验等横切逻辑，不建议隐藏复杂业务流程。
