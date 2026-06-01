import queue
import threading
import time


def demo_event() -> None:
    print("\n=== Event：等待启动信号 ===")
    started = threading.Event()

    def worker() -> None:
        print("worker: 等待启动信号")
        started.wait()
        print("worker: 收到信号，开始工作")

    thread = threading.Thread(target=worker)
    thread.start()
    time.sleep(0.2)
    print("main: 发出启动信号")
    started.set()
    thread.join()


def demo_condition() -> None:
    print("\n=== Condition：等待库存变化 ===")
    condition = threading.Condition()
    stock = {"count": 0}

    def consumer() -> None:
        with condition:
            while stock["count"] == 0:
                print("consumer: 没有库存，进入等待")
                condition.wait()
            stock["count"] -= 1
            print("consumer: 消费一个库存")

    def producer() -> None:
        time.sleep(0.2)
        with condition:
            stock["count"] += 1
            print("producer: 增加库存并通知消费者")
            condition.notify()

    threads = [threading.Thread(target=consumer), threading.Thread(target=producer)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def demo_queue() -> None:
    print("\n=== Queue：生产者消费者 ===")
    tasks: queue.Queue[int | None] = queue.Queue()

    def producer() -> None:
        for item in range(3):
            print(f"producer: 放入任务 {item}")
            tasks.put(item)
        tasks.put(None)

    def consumer() -> None:
        while True:
            item = tasks.get()
            try:
                if item is None:
                    print("consumer: 收到停止信号")
                    return
                print(f"consumer: 处理任务 {item}")
                time.sleep(0.1)
            finally:
                tasks.task_done()

    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)
    consumer_thread.start()
    producer_thread.start()

    tasks.join()
    producer_thread.join()
    consumer_thread.join()


def main() -> None:
    demo_event()
    demo_condition()
    demo_queue()


if __name__ == "__main__":
    main()
