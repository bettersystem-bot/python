# 03 第一个 Kitex 服务

## 学习目标

- 从 IDL 开始创建一个最小 Echo 服务。
- 理解 `kitex -module ... -service ...` 生成了什么。
- 编写 Handler 和本地直连 Client。

## 第一步：定义 IDL

创建 `echo.thrift`：

```thrift
namespace go echo

struct EchoRequest {
    1: required string message
    2: optional string request_id
}

struct EchoResponse {
    1: required string message
}

service EchoService {
    EchoResponse Echo(1: EchoRequest req)
}
```

`namespace go echo` 决定生成的 Go 包路径片段。字段编号如 `1:`、`2:` 会参与序列化，发布后不能随意改。

## 第二步：生成 Server 代码

```bash
kitex -module hello-kitex -service echo.service echo.thrift
```

参数含义：

- `-module hello-kitex`：当前 Go module 名称。
- `-service echo.service`：生成 Server 骨架并设置服务名。
- `echo.thrift`：IDL 文件路径。

生成后常见结构：

```text
hello-kitex/
├── echo.thrift
├── go.mod
├── handler.go
├── main.go
└── kitex_gen/
    └── echo/
        ├── echo.go
        └── echoservice/
            ├── client.go
            └── server.go
```

不要手动修改 `kitex_gen`。IDL 变更后重新生成代码。

## 第三步：实现 Handler

```go
package main

import (
    "context"
    "fmt"

    "hello-kitex/kitex_gen/echo"
)

type EchoServiceImpl struct{}

func (s *EchoServiceImpl) Echo(
    ctx context.Context,
    req *echo.EchoRequest,
) (*echo.EchoResponse, error) {
    return &echo.EchoResponse{
        Message: fmt.Sprintf("server received: %s", req.Message),
    }, nil
}
```

Handler 只处理业务逻辑，不需要手写网络收发、编解码、连接池等框架逻辑。

## 第四步：启动 Server

```go
package main

import (
    "log"
    "net"

    "hello-kitex/kitex_gen/echo/echoservice"
    "github.com/cloudwego/kitex/server"
)

func main() {
    addr, _ := net.ResolveTCPAddr("tcp", "127.0.0.1:8888")

    svr := echoservice.NewServer(
        new(EchoServiceImpl),
        server.WithServiceAddr(addr),
    )

    if err := svr.Run(); err != nil {
        log.Fatal(err)
    }
}
```

本地教学使用固定地址是为了降低依赖；线上服务通常会接入服务注册、发现、监控、日志和配置平台。

## 第五步：编写 Client

```go
package main

import (
    "context"
    "log"
    "time"

    "hello-kitex/kitex_gen/echo"
    "hello-kitex/kitex_gen/echo/echoservice"
    "github.com/cloudwego/kitex/client"
)

func main() {
    cli, err := echoservice.NewClient(
        "echo.service",
        client.WithHostPorts("127.0.0.1:8888"),
        client.WithRPCTimeout(200*time.Millisecond),
        client.WithConnectTimeout(100*time.Millisecond),
    )
    if err != nil {
        log.Fatal(err)
    }

    req := &echo.EchoRequest{
        Message:   "hello kitex",
        RequestId: "demo-001",
    }

    resp, err := cli.Echo(context.Background(), req)
    if err != nil {
        log.Fatal(err)
    }

    log.Printf("response: %s", resp.Message)
}
```

## 检查点

- 能说清楚 IDL、`kitex_gen`、Handler、Client 的关系。
- 知道 `WithHostPorts` 是本地直连教学用法，不是线上服务发现方案。
- 知道超时应该显式配置，避免调用无限等待。
