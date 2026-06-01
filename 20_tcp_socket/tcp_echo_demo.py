import socket
import threading


HOST = "127.0.0.1"


def run_echo_server(ready_event: threading.Event, port_holder: list[int]) -> None:
    # AF_INET 表示 IPv4，SOCK_STREAM 表示 TCP。
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # 绑定到端口 0，表示让操作系统自动分配一个可用端口。
        server_socket.bind((HOST, 0))
        server_socket.listen()

        port = server_socket.getsockname()[1]
        port_holder.append(port)
        print(f"server: 监听 {HOST}:{port}")
        ready_event.set()

        # accept 会阻塞等待客户端连接，返回一个新的连接 socket。
        connection, address = server_socket.accept()
        with connection:
            print(f"server: 客户端已连接 {address}")

            while True:
                # recv 返回 bytes。TCP 是字节流，不是字符串流。
                data = connection.recv(1024)
                if not data:
                    print("server: 客户端关闭连接")
                    break

                message = data.decode("utf-8")
                print(f"server: 收到 {message!r}")

                # sendall 会尽量把所有字节都发送出去，比 send 更适合初学示例。
                connection.sendall(f"echo: {message}".encode("utf-8"))


def run_client(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # connect 主动连接服务端。
        client_socket.connect((HOST, port))

        for message in ["hello", "tcp", "socket"]:
            print(f"client: 发送 {message!r}")
            client_socket.sendall(message.encode("utf-8"))

            response = client_socket.recv(1024)
            print(f"client: 收到 {response.decode('utf-8')!r}")


def main() -> None:
    ready_event = threading.Event()
    port_holder: list[int] = []

    server_thread = threading.Thread(target=run_echo_server, args=(ready_event, port_holder))
    server_thread.start()

    ready_event.wait()
    run_client(port_holder[0])
    server_thread.join()


if __name__ == "__main__":
    main()
