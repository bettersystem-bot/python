import threading
import time


class BankAccount:
    def __init__(self) -> None:
        self.balance = 0
        self.lock = threading.Lock()

    def deposit(self, amount: int) -> None:
        # Lock 保护余额读写，避免多个线程同时修改 balance。
        with self.lock:
            old_balance = self.balance
            time.sleep(0.01)
            self.balance = old_balance + amount


class NestedCalculator:
    def __init__(self) -> None:
        # RLock 允许同一个线程重复进入同一把锁保护的区域。
        self.lock = threading.RLock()
        self.value = 0

    def add_twice(self) -> None:
        with self.lock:
            self.add_once()
            self.add_once()

    def add_once(self) -> None:
        # 如果这里用普通 Lock，add_twice 已经持有锁时再次进入会死锁。
        with self.lock:
            self.value += 1


def limited_worker(name: str, limiter: threading.Semaphore) -> None:
    # Semaphore 控制最多有几个线程能同时进入下面这段工作区。
    with limiter:
        print(f"{name}: 获得资源")
        time.sleep(0.3)
        print(f"{name}: 释放资源")


def demo_lock() -> None:
    print("\n=== Lock 保护共享余额 ===")
    account = BankAccount()
    threads = [threading.Thread(target=account.deposit, args=(10,)) for _ in range(5)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print(f"最终余额: {account.balance}")


def demo_rlock() -> None:
    print("\n=== RLock 支持同一线程重复进入 ===")
    calculator = NestedCalculator()
    calculator.add_twice()
    print(f"计算结果: {calculator.value}")


def demo_semaphore() -> None:
    print("\n=== Semaphore 限制并发数量 ===")
    limiter = threading.Semaphore(2)
    threads = [threading.Thread(target=limited_worker, args=(f"worker-{index}", limiter)) for index in range(5)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def main() -> None:
    demo_lock()
    demo_rlock()
    demo_semaphore()


if __name__ == "__main__":
    main()
