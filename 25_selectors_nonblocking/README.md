# 25 非阻塞 I/O 与 selectors

## 这一章学什么

线程并发是一种方式，但网络编程还有另一条路线：非阻塞 I/O + 事件循环。

`selectors` 是 Python 标准库对 select、poll、epoll、kqueue 等系统能力的统一封装。

你会学到：

- 非阻塞 socket 是什么
- selector 如何监听“可读事件”
- 事件驱动和 asyncio 的关系

## 直觉理解

阻塞模型像服务员站在一桌旁边等客人点菜。

非阻塞 + selector 像服务员看一个叫号屏幕：哪桌准备好了，就去哪桌处理。

## 运行方式

```bash
python3.10 25_selectors_nonblocking/selectors_demo.py
```
