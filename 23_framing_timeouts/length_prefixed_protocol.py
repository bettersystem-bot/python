import json
import socket
import struct
import threading
from typing import Any


HOST = "127.0.0.1"
HEADER_SIZE = 4


def send_message(sock: socket.socket, payload: dict[str, Any]) -> None:
    # 网络只能传 bytes，所以先把 Python dict 序列化成 JSON，再编码成 bytes。
    body = json.dumps(payload).encode("utf-8")

    # 使用 4 字节无符号整数表示正文长度。!I 表示网络字节序 unsigned int。
    header = struct.pack("!I", len(body))
    sock.sendall(header + body)


def recv_exactly(sock: socket.socket, size: int) -> bytes:
    # recv(size) 不保证一次拿满 size 字节，所以要循环读取。
    chunks = []
    remaining = size

    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("连接提前关闭")
        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def recv_message(sock: socket.socket) -> dict[str, Any]:
    # 先读固定 4 字节长度头。
    header = recv_exactly(sock, HEADER_SIZE)
    body_size = struct.unpack("!I", header)[0]

    # 再按长度读取完整正文。
    body = recv_exactly(sock, body_size)
    return json.loads(body.decode("utf-8"))


def run_server(ready_event: threading.Event, port_holder: list[int]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, 0))
        server_socket.listen()
        port_holder.append(server_socket.getsockname()[1])
        ready_event.set()

        connection, _ = server_socket.accept()
        with connection:
            connection.settimeout(2.0)
            request = recv_message(connection)
            print(f"server: 收到完整消息 {request}")
            send_message(connection, {"ok": True, "received": request})


def run_client(port: int) -> None:
    with socket.create_connection((HOST, port), timeout=2.0) as client_socket:
        client_socket.settimeout(2.0)
        send_message(client_socket, {"action": "ping", "number": 1})
        response = recv_message(client_socket)
        print(f"client: 收到完整响应 {response}")


def main() -> None:
    ready_event = threading.Event()
    port_holder: list[int] = []
    server_thread = threading.Thread(target=run_server, args=(ready_event, port_holder))
    server_thread.start()

    ready_event.wait()
    run_client(port_holder[0])
    server_thread.join()


if __name__ == "__main__":
    main()
