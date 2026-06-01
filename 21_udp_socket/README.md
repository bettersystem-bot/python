# 21 UDP Socket 基础

## 这一章学什么

这一章用 UDP 写一个简单的 echo 示例。

你会学到：

- UDP 不需要 `listen()` 和 `accept()`
- UDP 用 `sendto()` 和 `recvfrom()`
- UDP 每次发送的是一个数据报
- UDP 不保证到达、不保证顺序、不保证不重复

## TCP 和 UDP 的直观差异

TCP 是“先建立连接，再持续通话”。

UDP 是“每次都直接发一张明信片”。

## 运行方式

```bash
python3.10 21_udp_socket/udp_echo_demo.py
```
