# 11 异步流式 I/O

## 这一章为什么要补

前面的示例大多用 `asyncio.sleep()` 模拟等待，这对理解调度很有帮助，但真实异步程序经常面对的是“流”。

流不是一次性完整到达的东西，而是像水管里的水一样，一点一点流过来。

典型场景：

- TCP 连接
- WebSocket 消息
- 日志实时消费
- 大文件分块读取
- 长连接协议

## 这一章学什么

你会学到：

- `asyncio.start_server()` 如何启动异步 TCP 服务
- `StreamReader` 如何读取数据
- `StreamWriter` 如何写入数据
- 为什么 `drain()` 是一种背压信号
- 如何优雅关闭连接

## `drain()` 的直觉

你可以把 `StreamWriter` 想象成一个水桶。

写入太快时，水桶可能装不下，`await writer.drain()` 的含义就是：“等水桶里的水被下游接走一些，我再继续倒。”

这就是流式 I/O 里的背压思想。

## 运行方式

```bash
python3.10 11_streams/stream_echo_demo.py
```

这个示例会在本机启动一个临时 TCP echo server，然后用 client 发几条消息，最后自动关闭。

## 练习建议

- 增加更多消息
- 故意不调用 `drain()`，理解为什么真实代码不推荐
- 修改 server 返回格式
- 尝试同时启动多个 client
