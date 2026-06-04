# Go Kitex 框架学习路线

这套材料面向已经会写基础 Go 代码、但刚开始接触 RPC 和 Kitex 的同学。目标不是把所有线上治理细节一次讲完，而是先建立一条清晰链路：

> IDL 定义接口契约 → kitex 生成代码 → Server 实现 Handler → Client 发起 RPC → 配置超时/重试/中间件 → 排查常见问题

## 学习边界

- 本材料以公司内部 Kitex 使用方式为主，代码生成工具版本应以 `kitex -version` 输出的 `v1.x.x` 内部版本为准。
- 示例使用本地直连 `127.0.0.1:8888`，避免依赖真实服务发现、注册中心、配置中心或内部运行环境。
- 如果你当前无法完整运行 Go / Kitex 环境，也可以通过阅读 IDL、生成命令、Handler、Client 调用和排障清单完成核心学习。

## 推荐学习顺序

1. [`00-go-rpc-basics`](00-go-rpc-basics/README.md)：先理解 RPC、IDL、Client/Server。
2. [`01-kitex-overview`](01-kitex-overview/README.md)：理解 Kitex 在微服务通信中的定位。
3. [`02-environment-setup`](02-environment-setup/README.md)：准备 Go、Kitex Tool、Thriftgo。
4. [`03-first-kitex-service`](03-first-kitex-service/README.md)：完成第一个 Echo 服务的完整链路。
5. [`04-thrift-idl`](04-thrift-idl/README.md)：学会设计 Thrift IDL 和兼容性规则。
6. [`05-code-generation`](05-code-generation/README.md)：理解生成代码目录和命令参数。
7. [`06-client-server-development`](06-client-server-development/README.md)：实现 Handler、编写 Client、处理错误。
8. [`07-service-governance-basics`](07-service-governance-basics/README.md)：建立服务治理基本认知。
9. [`08-debugging-common-errors`](08-debugging-common-errors/README.md)：掌握常见问题排查路径。

## 最小示例

- IDL 示例：[`examples/hello_thrift/echo.thrift`](examples/hello_thrift/echo.thrift)
- 示例说明：[`examples/hello_thrift/README.md`](examples/hello_thrift/README.md)

## 学完后你应该能做到

- 解释 Kitex、RPC、IDL、`kitex_gen` 分别是什么。
- 写出一个简单 Thrift service，并知道哪些字段变更是兼容的。
- 使用 `kitex -module ... -service ... xxx.thrift` 生成服务端骨架。
- 知道业务逻辑应该写在 Handler，不应该手动修改生成代码。
- 编写一个本地直连 Client，并配置基础超时。
- 判断什么时候可以开启重试，什么时候不能盲目重试。
- 遇到超时、连接失败、IDL 不匹配、版本差异时，有基本排查顺序。
