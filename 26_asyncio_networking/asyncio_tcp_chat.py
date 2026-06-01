import asyncio


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    address = writer.get_extra_info("peername")
    print(f"async server: 新连接 {address}")

    try:
        while True:
            # readline 表示我们选择“换行符”作为消息边界。
            data = await reader.readline()
            if not data:
                break

            message = data.decode("utf-8").strip()
            print(f"async server: 收到 {message!r}")
            writer.write(f"echo: {message}\n".encode("utf-8"))
            await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()
        print("async server: 连接关闭")


async def run_client(name: str, host: str, port: int) -> None:
    reader, writer = await asyncio.open_connection(host, port)

    writer.write(f"{name} says hello\n".encode("utf-8"))
    await writer.drain()

    response = await reader.readline()
    print(f"async client {name}: 收到 {response.decode('utf-8').strip()!r}")

    writer.close()
    await writer.wait_closed()


async def main() -> None:
    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()
    print(f"async server: 监听 {host}:{port}")

    async with server:
        await asyncio.gather(
            run_client("client-1", host, port),
            run_client("client-2", host, port),
            run_client("client-3", host, port),
        )
        server.close()
        await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
