# 04 Thrift IDL：接口契约与兼容性

## 学习目标

- 掌握 Thrift IDL 的基础结构。
- 理解字段编号、字段类型、required / optional。
- 判断常见字段变更是否兼容。

## 基础语法

```thrift
namespace go user

struct GetUserRequest {
    1: required i64 user_id
    2: optional string request_id
}

struct User {
    1: required i64 user_id
    2: required string name
    3: optional string email
}

struct GetUserResponse {
    1: optional User user
    255: optional BaseResp base_resp
}

service UserService {
    GetUserResponse GetUser(1: GetUserRequest req)
}
```

常见类型：

- 基础类型：`bool`、`byte`、`i16`、`i32`、`i64`、`double`、`string`、`binary`。
- 容器类型：`list<T>`、`set<T>`、`map<K,V>`。
- 自定义类型：`struct`、`exception`。

## 字段编号规则

字段编号参与序列化协议，是跨版本兼容的关键。

推荐：

- 常用字段使用 `1-20`。
- 普通字段使用后续编号并预留空间。
- 公司内部常见约定中，`255` 可用于 `Base` / `BaseResp` 类字段。
- 字段发布后不要修改编号、复用编号或改变字段含义。

## 兼容性判断

| 变更 | 是否推荐 | 原因 |
| --- | --- | --- |
| 新增 `optional` 字段 | 推荐 | 老 Client / Server 可忽略未知字段 |
| 删除未使用的 `optional` 字段 | 谨慎 | 老版本可能仍在发送或读取 |
| 修改字段编号 | 禁止 | 会破坏序列化兼容 |
| 修改字段类型 | 禁止 | 老版本无法正确解析 |
| 把 `optional` 改成 `required` | 不推荐 | 老版本可能不传该字段 |
| 复用已废弃字段编号 | 禁止 | 老数据可能被解释成新含义 |

## required 和 optional 的取舍

初学者容易把所有字段都写成 `required`。更稳妥的做法是：

- 确实构成请求最小语义的字段才考虑 `required`。
- 后续新增字段优先使用 `optional`。
- 响应里的扩展字段优先使用 `optional`，降低灰度和回滚风险。

## 练习

阅读 [`../examples/hello_thrift/echo.thrift`](../examples/hello_thrift/echo.thrift)，回答：

1. 如果新增 `caller` 字段，应该使用哪个新字段编号？
2. 能不能把 `message` 的编号从 `1` 改成 `3`？为什么？
3. `request_id` 为什么适合设计成 `optional`？
