# Gateway Monitor

OpenClaw Gateway 监控与自动恢复系统

## 项目简介

Gateway Monitor 是一个用于监控 OpenClaw Gateway 服务状态的 Python 脚本。它可以实时检测 Gateway 服务是否正常运行，并在服务异常时自动尝试恢复，同时通过飞书发送通知告警。

## 功能特点

- 🔍 **实时监控** - 每隔指定时间检查 Gateway 端口连通性
- 🔄 **自动重启** - 服务异常时自动执行重启命令
- 📢 **飞书通知** - 支持通过飞书 Webhook 发送告警通知
- 📝 **日志记录** - 自动记录监控日志，便于排查问题

## 安装说明

### 环境要求

- Python 3.7+
- 已安装 OpenClaw

### 安装步骤

1. 克隆仓库：

```bash
git clone https://github.com/sidaotiger/gateway-monitor.git
cd gateway-monitor
```

2. 确保 Python 环境可用：

```bash
python3 --version
```

## 配置说明

编辑 `gateway_monitor.py` 文件中的配置项：

```python
# Gateway 连接配置
GATEWAY_HOST = "127.0.0.1"      # Gateway 主机地址
GATEWAY_PORT = 18789            # Gateway 端口
CHECK_INTERVAL = 30            # 检查间隔（秒）
TIMEOUT = 5                     # 连接超时（秒）

# 自动重启配置
AUTO_RESTART = True            # 是否启用自动重启
RESTART_WAIT = 10              # 重启后等待时间（秒）

# 飞书通知配置
FEISHU_WEBHOOK_URL = "YOUR_FEISHU_WEBHOOK_URL"  # 替换为你的飞书 Webhook 地址
```

### 获取飞书 Webhook 地址

1. 在飞书群聊中点击右上角「...」→「添加群机器人」
2. 选择「自定义机器人」
3. 设置机器人名称，复制 Webhook 地址
4. 将地址填入配置中的 `FEISHU_WEBHOOK_URL`

## 运行说明

### 方式一：直接运行

```bash
python3 gateway_monitor.py
```

### 方式二：后台运行（Linux/macOS）

```bash
nohup python3 gateway_monitor.py > gateway_monitor.log 2>&1 &
```

### 方式三：使用 systemd（Linux）

创建服务文件 `/etc/systemd/system/gateway-monitor.service`：

```ini
[Unit]
Description=OpenClaw Gateway Monitor
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/gateway-monitor
ExecStart=/usr/bin/python3 /path/to/gateway-monitor/gateway_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable gateway-monitor
sudo systemctl start gateway-monitor
```

### 方式四：Windows 任务计划

1. 创建一个 `.bat` 文件：
```batch
python.exe "C:\path\to\gateway-monitor\gateway_monitor.py"
```

2. 打开「任务计划程序」→ 创建基本任务 → 按指引添加

## 项目结构

```
gateway-monitor/
├── README.md              # 本文件
├── gateway_monitor.py     # 主程序
└── .gitignore            # Git 忽略配置
```

## 技术栈

- **Python 3** - 脚本语言
- **socket** - TCP 连接检测
- **subprocess** - 执行系统命令
- **urllib** - 飞书 Webhook HTTP 请求
- **logging** - 日志记录
- **飞书机器人 API** - 消息通知

## 许可证

MIT License

## 作者

[sidaotiger](https://github.com/sidaotiger)
