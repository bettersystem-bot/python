# 22 HTTP 基础

## 这一章学什么

HTTP 是建立在 TCP 之上的应用层协议。

这一章不引入第三方框架，只用标准库帮助你理解 HTTP 的本质。

你会学到：

- HTTP 请求和响应大概长什么样
- 如何用 `http.server` 启动本地 HTTP 服务
- 如何用 `urllib.request` 发起 HTTP 请求
- header、status code、body 分别是什么

## HTTP 本质

HTTP 本质上是一套文本协议约定。

一次请求通常包含：

- 请求方法：GET、POST 等
- 路径：例如 `/hello`
- 请求头：例如 `User-Agent`
- 请求体：可选

一次响应通常包含：

- 状态码：例如 200、404、500
- 响应头
- 响应体

## 运行方式

```bash
python3.10 22_http_basics/http_server_client_demo.py
```
