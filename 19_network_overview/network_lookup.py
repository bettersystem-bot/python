import socket


def main() -> None:
    # hostname 是当前机器在系统层面的主机名。
    hostname = socket.gethostname()
    print(f"当前主机名: {hostname}")

    # getaddrinfo 是更通用的地址解析 API，可以同时返回 IPv4 / IPv6 等信息。
    print("\nlocalhost 地址解析结果:")
    results = socket.getaddrinfo("localhost", 80, type=socket.SOCK_STREAM)

    for family, socktype, proto, canonname, sockaddr in results:
        print(
            f"family={family}, socktype={socktype}, "
            f"proto={proto}, canonname={canonname!r}, sockaddr={sockaddr}"
        )

    # 127.0.0.1 是回环地址，网络包不会真的离开本机，适合学习和测试。
    print("\n127.0.0.1 是本机回环地址，适合做网络编程练习。")


if __name__ == "__main__":
    main()
