import socket
import socketserver
import threading


class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        # 每个客户端连接会进入一个独立的 handler。
        address = self.client_address
        print(f"server: 处理客户端 {address}")

        data = self.request.recv(1024)
        message = data.decode("utf-8")
        self.request.sendall(f"echo: {message}".encode("utf-8"))


def run_server(ready_event: threading.Event, address_holder: list[tuple[str, int]]) -> None:
    with socketserver.ThreadingTCPServer(("127.0.0.1", 0), EchoHandler) as server:
        host, port = server.server_address
        address_holder.append((host, port))
        print(f"server: 监听 {host}:{port}")
        ready_event.set()

        # handle_request 每次处理一个请求；因为 server 是 ThreadingTCPServer，请求处理会在线程中执行。
        for _ in range(3):
            server.handle_request()


def run_client(name: str, host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=2.0) as sock:
        sock.sendall(name.encode("utf-8"))
        response = sock.recv(1024).decode("utf-8")
        print(f"client {name}: 收到 {response!r}")


def main() -> None:
    ready_event = threading.Event()
    address_holder: list[tuple[str, int]] = []
    server_thread = threading.Thread(target=run_server, args=(ready_event, address_holder))
    server_thread.start()

    ready_event.wait()
    host, port = address_holder[0]

    clients = [threading.Thread(target=run_client, args=(f"client-{index}", host, port)) for index in range(3)]
    for client in clients:
        client.start()
    for client in clients:
        client.join()

    server_thread.join()


if __name__ == "__main__":
    main()
