import asyncio


class AsyncCounter:
    def __init__(self, limit: int) -> None:
        self.current = 0
        self.limit = limit

    def __aiter__(self):
        return self

    async def __anext__(self) -> int:
        if self.current >= self.limit:
            raise StopAsyncIteration
        await asyncio.sleep(0.2)
        self.current += 1
        return self.current


async def sensor_stream(limit: int):
    for value in range(limit):
        await asyncio.sleep(0.15)
        yield {"reading": value, "unit": "demo"}


class FakeConnection:
    async def __aenter__(self):
        print("FakeConnection: opening connection")
        await asyncio.sleep(0.2)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        print("FakeConnection: closing connection")
        await asyncio.sleep(0.2)
        return False

    async def send(self, payload: str) -> None:
        await asyncio.sleep(0.1)
        print(f"FakeConnection: sent {payload}")


async def main() -> None:
    print("\n=== async iterator ===")
    async for number in AsyncCounter(limit=3):
        print("counter value:", number)

    print("\n=== async generator ===")
    async for reading in sensor_stream(limit=4):
        print("stream reading:", reading)

    print("\n=== async context manager ===")
    async with FakeConnection() as connection:
        await connection.send("hello async world")


if __name__ == "__main__":
    asyncio.run(main())
