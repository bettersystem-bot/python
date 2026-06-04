# 07 服务治理基础：超时、重试、负载均衡、发现

## 学习目标

- 理解服务治理解决的是生产稳定性问题。
- 掌握超时和重试的基础配置原则。
- 建立服务发现、负载均衡、中间件的基本概念。

## 超时

常见两类：

```go
client.WithConnectTimeout(100 * time.Millisecond) // 建立连接超时
client.WithRPCTimeout(200 * time.Millisecond)     // 单次 RPC 总超时
```

配置建议：

- 不要不设超时。
- 不要随意写很大的超时。
- 可根据下游 P99 延迟加安全余量，例如 P99 80ms，超时设置 100ms 起步评估。
- 调用链中要关注剩余时间，避免上游已超时、下游还在做无意义工作。

## 重试

```go
fp := retry.NewFailurePolicy()
fp.WithMaxRetryTimes(1)       // 失败后最多重试 1 次，加首次共最多 2 次请求
fp.WithMaxDurationMS(500)     // 控制总耗时
fp.WithFixedBackOff(50 * time.Millisecond)

cli, err := echoservice.NewClient(
    "echo.service",
    client.WithFailureRetry(fp),
)
```

重试原则：

- 只对幂等接口谨慎开启，如查询、读操作。
- 下单、扣款、发券等非幂等接口不要盲目失败重试。
- 重试会放大流量，故障时可能压垮下游。
- 设置最大次数、总耗时和退避策略。

## 服务发现

本地教学用：

```go
client.WithHostPorts("127.0.0.1:8888")
```

线上通常不硬编码地址，而是通过服务名查找可用实例：

```text
Client 按 service name 请求
  ↓
服务发现返回实例列表
  ↓
负载均衡选择一个实例
  ↓
发起 RPC
```

## 负载均衡

负载均衡决定一次请求发到哪个实例。常见策略：

- 加权随机：通用、简单。
- 加权轮询：更均匀。
- 一致性哈希：适合本地缓存、会话保持、分片场景。

## 中间件

中间件形成洋葱模型：

```text
请求: MW1 → MW2 → Handler / RPC
响应: MW1 ← MW2 ← Handler / RPC
```

适合放：

- 日志。
- 指标上报。
- 链路追踪。
- 鉴权。
- 限流或熔断入口。

## 初学者常见错误

- 没有超时，调用卡住后难以定位。
- 为非幂等接口开启重试。
- 本地 `WithHostPorts` 直接照搬到线上。
- 在中间件里写复杂业务逻辑。
- 只看 Client 失败，不检查服务发现、负载均衡和下游实例状态。
