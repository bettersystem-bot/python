import http.server
import json
import threading
import urllib.request


class DemoHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        # do_GET 会处理 HTTP GET 请求。
        if self.path != "/hello":
            self.send_error(404, "Not Found")
            return

        body = json.dumps({"message": "hello http"}).encode("utf-8")

        # 状态行：200 表示请求成功。
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        # wfile 是响应体输出流。
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        # 覆盖默认日志，避免示例输出太杂。
        pass


def run_server(ready_event: threading.Event, port_holder: list[int]) -> None:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
    port = server.server_address[1]
    port_holder.append(port)
    print(f"http server: 监听 127.0.0.1:{port}")
    ready_event.set()

    # 只处理一个请求，方便示例自动结束。
    server.handle_request()
    server.server_close()


def run_client(port: int) -> None:
    url = f"http://127.0.0.1:{port}/hello"

    with urllib.request.urlopen(url, timeout=2.0) as response:
        status = response.status
        content_type = response.headers.get("Content-Type")
        body = response.read().decode("utf-8")

    print(f"client: status={status}")
    print(f"client: content-type={content_type}")
    print(f"client: body={body}")


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
