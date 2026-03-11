# Gateway Monitor

[English](#english) | [中文](#中文) | [日本語](#日本語)

---

## English

### Overview
OpenClaw Gateway monitoring program with auto-restart and Feishu notification.

### Features
- 🌐 Real-time Gateway status monitoring
- 🔄 Auto-restart when Gateway is down
- 📱 Feishu notification on status change
- 🖥️ GUI interface with system tray
- ⚡ Single instance running

### Installation

```bash
# Clone the repository
git clone https://github.com/sidaotiger/gateway-monitor.git
cd gateway-monitor

# Run the monitor
python gateway_monitor.py
```

### Configuration
- Default check interval: 30 seconds
- Default port: 18789
- Auto-restart: Enabled

### Requirements
- Python 3.8+
- requests
- tkinter (included in Python)
- pystray

---

## 中文

### 概述
OpenClaw Gateway 监控程序，支持自动重启和飞书通知。

### 功能
- 🌐 实时监控 Gateway 状态
- 🔄 Gateway 宕机自动重启
- 📱 飞书通知状态变化
- 🖥️ GUI 界面 + 系统托盘
- ⚡ 单实例运行

### 安装

```bash
# 克隆仓库
git clone https://github.com/sidaotiger/gateway-monitor.git
cd gateway-monitor

# 运行监控程序
python gateway_monitor.py
```

### 配置
- 默认检查间隔：30秒
- 默认端口：18789
- 自动重启：已开启

### 环境要求
- Python 3.8+
- requests
- tkinter（Python自带）
- pystray

---

## 日本語

### 概要
OpenClaw Gateway 監視プログラム自動再起動とFeishu通知付き。

### 機能
- 🌐 Gatewayリアルタイム監視
- 🔄 自動再起動
- 📱 Feishu通知
- 🖥️ GUIインターフェース
- ⚡ シングルインスタンス

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/sidaotiger/gateway-monitor.git
cd gateway-monitor

# 監視プログラムを実行
python gateway_monitor.py
```

### 設定
- デフォルト確認間隔：30秒
- デフォルトポート：18789
- 自動再起動：有効

### 環境要件
- Python 3.8+
- requests
- tkinter（Pythonに付属）
- pystray
