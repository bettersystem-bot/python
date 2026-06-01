import threading
import time


class UnsafeCounter:
    def __init__(self) -> None:
        self.value = 0

    def increase(self) -> None:
        # 故意拆开读、改、写三个步骤，并插入 sleep，放大线程切换导致的问题。
        current = self.value
        time.sleep(0.0001)
        self.value = current + 1


class SafeCounter:
    def __init__(self) -> None:
        self.value = 0
        self.lock = threading.Lock()

    def increase(self) -> None:
        # with lock 会保证同一时刻只有一个线程能进入这段临界区。
        with self.lock:
            current = self.value
            time.sleep(0.0001)
            self.value = current + 1


def run_threads(counter, thread_count: int, loops: int) -> int:
    def worker() -> None:
        for _ in range(loops):
            counter.increase()

    threads = [threading.Thread(target=worker) for _ in range(thread_count)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    return counter.value


def main() -> None:
    thread_count = 10
    loops = 100
    expected = thread_count * loops

    unsafe_result = run_threads(UnsafeCounter(), thread_count, loops)
    print(f"不加锁结果: {unsafe_result}, 预期: {expected}")

    safe_result = run_threads(SafeCounter(), thread_count, loops)
    print(f"加锁后结果: {safe_result}, 预期: {expected}")


if __name__ == "__main__":
    main()
