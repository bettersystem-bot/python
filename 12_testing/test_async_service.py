import asyncio
import unittest


async def fetch_profile(user_id: int, delay: float = 0.05) -> dict:
    # 这个函数模拟一个异步服务调用。
    # 测试时我们把 delay 设计得很短，避免测试跑得太慢。
    await asyncio.sleep(delay)

    if user_id <= 0:
        raise ValueError("user_id 必须是正整数")

    return {"user_id": user_id, "name": f"user-{user_id}"}


class FetchProfileTest(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_profile_success(self) -> None:
        # 成功路径：验证返回结构和关键字段。
        profile = await fetch_profile(7)
        self.assertEqual(profile["user_id"], 7)
        self.assertEqual(profile["name"], "user-7")

    async def test_fetch_profile_invalid_user_id(self) -> None:
        # 异常路径：异步测试里同样可以使用 assertRaises。
        with self.assertRaises(ValueError):
            await fetch_profile(0)

    async def test_fetch_profile_timeout(self) -> None:
        # 超时路径：用 wait_for 包住被测协程，验证它在太慢时会被取消。
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(fetch_profile(1, delay=0.2), timeout=0.01)


if __name__ == "__main__":
    unittest.main()
