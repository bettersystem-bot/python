import selectors
import socket
import threading


HOST = "127.0.0.1"


def run_selector_server(ready_event: threading.Event, port_holder: list[int]) -> None:
    selector = selectors.DefaultSelector()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, 0))
    server_socket.listen()
    server_socket.setblocking(False)

    port_holder.append(server_socket.getsockname()[1])
    print(f"selector server: 监听 {HOST}:{port_holder[0]}")

    # 注册 server_socket 的可读事件。服务端 socket 可读表示有新连接可以 accept。
    selector.register(server_socket, selectors.EVENT_READ, data="server")
    ready_event.set()

    handled_clients = 0
    try:
        while handled_clients < 2:
            events = selector.select(timeout=2.0)
            for key, _ in events:
                if key.data == "server":
                    connection, address = server_socket.accept()
                    print(f"selector server: 新连接 {address}")
                    connection.setblocking(False)
                    selector.register(connection, selectors.EVENT_READ, data="client")
                else:
                    connection = key.fileobj
                    data = connection.recv(1024)
                    if data:
                        connection.sendall(b"echo: " + data)
                        handled_clients += 1
                    selector.unregister(connection)
                    connection.close()
    finally:
        selector.close()
        server_socket.close()


def run_client(name: str, port: int) -> None:
    with socket.create_connection((HOST, port), timeout=2.0) as sock:
        sock.sendall(name.encode("utf-8"))
        response = sock.recv(1024).decode("utf-8")
        print(f"client {name}: 收到 {response!r}")


def main() -> None:
    ready_event = threading.Event()
    port_holder: list[int] = []
    server_thread = threading.Thread(target=run_selector_server, args=(ready_event, port_holder))
    server_thread.start()

    ready_event.wait()
    clients = [threading.Thread(target=run_client, args=(f"client-{index}", port_holder[0])) for index in range(2)]
    for client in clients:
        client.start()
    for client in clients:
        client.join()

    server_thread.join()


if __name__ == "__main__":
    main()
