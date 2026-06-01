import socket
import threading


HOST = "127.0.0.1"


def run_udp_server(ready_event: threading.Event, port_holder: list[int]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind((HOST, 0))
        port = server_socket.getsockname()[1]
        port_holder.append(port)
        print(f"udp server: 监听 {HOST}:{port}")
        ready_event.set()

        for _ in range(3):
            # recvfrom 会同时返回数据和发送方地址。
            data, address = server_socket.recvfrom(1024)
            message = data.decode("utf-8")
            print(f"udp server: 收到 {message!r} from {address}")

            server_socket.sendto(f"echo: {message}".encode("utf-8"), address)


def run_udp_client(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.settimeout(2.0)

        for message in ["hello", "udp", "datagram"]:
            print(f"udp client: 发送 {message!r}")
            client_socket.sendto(message.encode("utf-8"), (HOST, port))

            data, address = client_socket.recvfrom(1024)
            print(f"udp client: 收到 {data.decode('utf-8')!r} from {address}")


def main() -> None:
    ready_event = threading.Event()
    port_holder: list[int] = []
    server_thread = threading.Thread(target=run_udp_server, args=(ready_event, port_holder))
    server_thread.start()

    ready_event.wait()
    run_udp_client(port_holder[0])
    server_thread.join()


if __name__ == "__main__":
    main()
