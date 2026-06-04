# 02 环境准备

## 学习目标

- 准备 Go module 项目。
- 安装并验证 Kitex 代码生成工具。
- 理解公司内部 Kitex 版本要求。

## 前置要求

```bash
go version
go env GOPATH
go env GOPRIVATE
```

公司内部项目通常还需要配置内部 Git 和 Go module 访问权限。遇到依赖拉取失败时，优先检查：

- 是否有内部网络 / 权限。
- `GOPRIVATE` / `GONOSUMDB` 是否包含内部域名。
- Git 是否能访问内部仓库。

## 安装 Kitex Tool

公司内部场景推荐：

```bash
go install code.byted.org/kite/kitex/tool/cmd/kitex@latest
```

验证：

```bash
kitex -version
```

输出应是公司内部 `v1.x.x` 版本。若网上教程使用的是开源版本命令或 API，内部项目以公司内部版本和现有服务代码为准。

## 安装 Thriftgo

Thrift IDL 场景需要：

```bash
go install github.com/cloudwego/thriftgo@latest
thriftgo --version
```

## 新建练习项目

```bash
mkdir hello-kitex
cd hello-kitex
go mod init hello-kitex
```

本仓库只保存教学材料和示例片段；真实运行时请在一个独立 Go module 练习目录里执行命令，避免把生成代码误提交到学习仓库。

## 常见问题

### `kitex: command not found`

通常是 `$GOPATH/bin` 没有加入 `PATH`：

```bash
export PATH="$PATH:$(go env GOPATH)/bin"
```

### 安装失败

按顺序检查：

1. Go 版本是否满足项目要求。
2. 内部依赖是否有访问权限。
3. `GOPRIVATE` / Git SSH 是否配置正确。
4. 是否需要使用内部文档指定的固定版本。
