#!/usr/bin/env python3
"""
OpenClaw Gateway 存活监控脚本
监控端口 18789，挂了发通知，支持自动重启
"""

import socket
import time
import logging
import subprocess
import urllib.request
import json
from datetime import datetime

# 配置
GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 18789
CHECK_INTERVAL = 30  # 秒
TIMEOUT = 5  # 连接超时秒数
AUTO_RESTART = True  # 是否自动重启
RESTART_WAIT = 10  # 重启后等待秒数再检查

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("gateway_monitor.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_gateway() -> bool:
    """检查 Gateway 是否存活"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((GATEWAY_HOST, GATEWAY_PORT))
        sock.close()
        return result == 0
    except Exception as e:
        logger.error(f"检查连接时出错: {e}")
        return False


# ===== 飞书配置 =====
# 在飞书群聊添加机器人后获取 Webhook 地址
FEISHU_WEBHOOK_URL = "YOUR_FEISHU_WEBHOOK_URL"  # 替换为你的飞书 Webhook 地址


def send_feishu(msg: str):
    """发送飞书消息"""
    if FEISHU_WEBHOOK_URL == "YOUR_FEISHU_WEBHOOK_URL":
        logger.warning("飞书 Webhook 未配置，跳过发送")
        return
    
    try:
        data = {
            "msg_type": "text",
            "content": {"text": msg}
        }
        req = urllib.request.Request(
            FEISHU_WEBHOOK_URL,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                logger.info("飞书消息发送成功")
            else:
                logger.error(f"飞书消息发送失败: {result}")
    except Exception as e:
        logger.error(f"发送飞书消息出错: {e}")


def send_notification(status: str):
    """发送通知"""
    msg = f"🚨 OpenClaw Gateway {status}！时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 打印到控制台
    print(msg)
    logger.warning(msg)
    
    # 发送飞书通知
    send_feishu(msg)


def restart_gateway() -> bool:
    """尝试重启 Gateway"""
    logger.info("正在执行自动重启...")
    try:
        # 执行 openclaw gateway start 命令
        result = subprocess.run(
            ["openclaw", "gateway", "start"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            logger.info(f"重启命令执行成功: {result.stdout}")
            return True
        else:
            logger.error(f"重启命令执行失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("重启命令执行超时")
        return False
    except FileNotFoundError:
        logger.error("未找到 openclaw 命令，请确保已安装")
        return False
    except Exception as e:
        logger.error(f"执行重启时出错: {e}")
        return False


def wait_for_gateway(wait_seconds: int = 10) -> bool:
    """等待 Gateway 启动并检查是否存活"""
    logger.info(f"等待 {wait_seconds} 秒后检查 Gateway 状态...")
    time.sleep(wait_seconds)
    return check_gateway()


def main():
    logger.info(f"开始监控 Gateway ({GATEWAY_HOST}:{GATEWAY_PORT})，间隔 {CHECK_INTERVAL} 秒")
    logger.info(f"自动重启功能: {'开启' if AUTO_RESTART else '关闭'}")
    
    is_alive = None  # 初始状态未知
    
    while True:
        alive = check_gateway()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if alive:
            logger.info(f"[{current_time}] Gateway 存活 ✓")
        else:
            logger.error(f"[{current_time}] Gateway 挂了 ✗")
            
            # 状态变化时通知（只在从存活变挂时通知，避免重复）
            if is_alive is True:
                send_notification("已下线")
            elif is_alive is None:
                send_notification("无法连接")
            
            # 自动重启
            if AUTO_RESTART:
                send_notification("正在尝试自动重启...")
                if restart_gateway():
                    # 等待后检查是否恢复
                    if wait_for_gateway(RESTART_WAIT):
                        success_msg = f"✅ 自动重启成功！时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        print(success_msg)
                        logger.info(success_msg)
                        send_feishu(success_msg)
                    else:
                        fail_msg = f"❌ 自动重启后Gateway仍未恢复！时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        print(fail_msg)
                        logger.error(fail_msg)
                        send_feishu(fail_msg)
                else:
                    fail_msg = f"❌ 自动重启命令执行失败！时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    print(fail_msg)
                    logger.error(fail_msg)
                    send_feishu(fail_msg)
        
        # 更新状态
        is_alive = alive
        
        # 等待下次检查
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
