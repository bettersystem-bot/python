# Hello Thrift 示例

这个目录保存最小 Echo 服务的 IDL。它用于教学，不直接保存 `kitex_gen` 生成代码。

## 练习命令

在独立 Go module 练习目录中复制 `echo.thrift` 后执行：

```bash
go mod init hello-kitex
kitex -module hello-kitex -service echo.service echo.thrift
```

然后按 [`../../03-first-kitex-service/README.md`](../../03-first-kitex-service/README.md) 实现 Handler、启动 Server、编写 Client。

## 设计说明

```thrift
struct EchoRequest {
    1: required string message
    2: optional string request_id
}
```

- `message` 是 Echo 的核心输入。
- `request_id` 是可选字段，适合讲解日志追踪、幂等和重试安全性。
- 字段编号发布后不能随意修改。

## 不提交生成代码的原因

生成代码与本机 Kitex Tool 版本、Go module 名称、依赖版本相关。教学仓库保留 IDL 和命令，避免把某个环境生成的代码误认为通用答案。
