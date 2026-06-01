# 23 消息边界、粘包拆包与超时

## 这一章为什么重要

TCP 是字节流协议，不是消息协议。

你发送两次：

```text
hello
world
```

接收方可能一次收到 `helloworld`，也可能分几次收到。TCP 只保证字节顺序，不保证你的业务消息边界。

## 常见解决方案

业务协议必须自己定义消息边界，常见方式有：

- 固定长度
- 分隔符，例如换行符 `\n`
- 长度前缀，例如先发 4 字节长度，再发正文

## 为什么必须设置 timeout

网络程序不能假设对方一定会回应。

如果没有 timeout，程序可能永远卡在：

- connect
- recv
- send
- accept

## 运行方式

```bash
python3.10 23_framing_timeouts/length_prefixed_protocol.py
```

这个示例用“4 字节长度前缀 + JSON 正文”的方式定义消息边界。
