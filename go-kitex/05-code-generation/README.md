# 05 代码生成：从 IDL 到 Go 代码

## 学习目标

- 理解 Kitex Tool 的输入和输出。
- 掌握 Client 代码和 Server 骨架的生成命令。
- 知道生成代码如何纳入版本管理和维护。

## 只生成 Client 可用代码

```bash
kitex -module hello-kitex echo.thrift
```

适合只需要调用下游服务的场景。通常会生成 `kitex_gen`，其中包含请求/响应类型和 Client 构造代码。

## 生成 Server 骨架

```bash
kitex -module hello-kitex -service echo.service echo.thrift
```

会生成：

- `kitex_gen/`：IDL 对应的类型、Client、Server 接口等生成代码。
- `handler.go`：业务 Handler 实现入口。
- `main.go`：Server 启动入口。
- 构建脚本或元信息文件（取决于工具版本）。

## 常用参数

| 参数 | 作用 |
| --- | --- |
| `-module` | 指定 Go module 名称，Go module 项目中推荐显式填写 |
| `-service` | 生成 Server 骨架并指定服务名，建议使用真实 PSM / 服务名 |
| `-I` | 添加 IDL 搜索路径，公共 IDL 或 include 场景常用 |
| `-gen-path` | 指定生成代码路径，默认通常是 `./kitex_gen` |
| `-use` | 复用外部生成代码，适合依赖公共 `kitex_gen` 的服务 |
| `-disable-self-update` | 禁用自动更新，生产或 CI 中更利于版本可控 |

## 生成代码维护原则

- 不要手动修改 `kitex_gen`。
- IDL 变更后重新执行生成命令。
- 生成代码建议进入版本管理，便于调用方编译和代码审查。
- 生产环境固定 Kitex Tool 版本，避免不同机器生成结果不一致。
- Thrift 场景遇到 `github.com/apache/thrift` API 不兼容时，按内部项目要求固定兼容版本。

## 看生成代码时重点看什么

初学阶段不需要读懂所有生成细节，先关注：

1. Request / Response Go struct 在哪里。
2. Service 接口的方法签名是什么。
3. `NewClient` / `MustNewClient` 在哪里。
4. `NewServer` 需要传入哪个 Handler 实现。

## 生成失败排查

按顺序检查：

1. `kitex -version` 是否是内部 `v1.x.x`。
2. 当前目录是否是正确 Go module。
3. `-module` 是否和 `go.mod` 一致。
4. IDL 语法是否错误，include 路径是否能找到。
5. `thriftgo` 是否安装并在 `PATH` 中。
6. 内部仓库或公共 IDL 是否有权限访问。
