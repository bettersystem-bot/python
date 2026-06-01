import multiprocessing
import os


def cpu_job(name: str, size: int, result_queue: multiprocessing.Queue) -> None:
    # 每个进程都有自己的 Python 解释器和内存空间。
    total = 0
    for number in range(size):
        total += number * number

    # 进程之间不能直接安全地改同一个普通变量，这里用 Queue 把结果传回主进程。
    result_queue.put((name, os.getpid(), total % 1_000_000))


def main() -> None:
    result_queue: multiprocessing.Queue = multiprocessing.Queue()
    processes = [
        multiprocessing.Process(target=cpu_job, args=(f"process-{index}", 500_000, result_queue))
        for index in range(2)
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    while not result_queue.empty():
        name, pid, result_tail = result_queue.get()
        print(f"{name}: pid={pid}, result_tail={result_tail}")


if __name__ == "__main__":
    # macOS 和 Windows 上多进程启动方式更依赖这个保护，务必养成习惯。
    main()
