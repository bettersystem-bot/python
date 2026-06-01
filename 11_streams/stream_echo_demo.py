import asyncio


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    # 每个客户端连接都会进入这个协程，服务端可以同时处理多个客户端。
    address = writer.get_extra_info("peername")
    print(f"server: 新连接 {address}")

    try:
        while True:
            # readline 会一直等待，直到读到换行符或连接关闭。
            data = await reader.readline()
            if not data:
                print("server: 客户端关闭连接")
                break

            message = data.decode().strip()
            print(f"server: 收到 {message!r}")

            response = f"echo: {message}\n"
            writer.write(response.encode())

            # drain 是流式写入里的背压点：如果发送缓冲区满了，这里会等待。
            await writer.drain()

    finally:
        # close 先发起关闭，wait_closed 等待底层连接真正关闭。
        writer.close()
        await writer.wait_closed()
        print("server: 连接已关闭")


async def run_client(host: str, port: int) -> None:
    # open_connection 返回一对 reader/writer，分别负责读和写。
    reader, writer = await asyncio.open_connection(host, port)

    messages = ["hello", "async", "stream"]
    for message in messages:
        print(f"client: 发送 {message!r}")
        writer.write(f"{message}\n".encode())
        await writer.drain()

        # 客户端等待服务端回显一行数据。
        response = await reader.readline()
        print(f"client: 收到 {response.decode().strip()!r}")

    writer.close()
    await writer.wait_closed()
    print("client: 连接已关闭")


async def main() -> None:
    # 端口设置为 0 表示让操作系统自动分配一个可用端口。
    server = await asyncio.start_server(handle_client, host="127.0.0.1", port=0)
    host, port = server.sockets[0].getsockname()
    print(f"server: 监听 {host}:{port}")

    async with server:
        # server.serve_forever() 会一直运行，所以这里用 client 跑完后手动关闭 server。
        await run_client(host, port)
        server.close()
        await server.wait_closed()

    print("demo 完成")


if __name__ == "__main__":
    asyncio.run(main())
