#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gateway 监控程序 - Windows GUI 版本
作者: 码哥
功能: 监控 OpenClaw Gateway 状态，支持托盘、告警、自动重启
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import sys
import subprocess
import requests
from datetime import datetime
import pystray
from PIL import Image, ImageDraw

# 飞书配置
FEISHU_APP_ID = "cli_a925035cf63bdbc6"
FEISHU_APP_SECRET = "WmscS2ApukEoSOZPKBo5Mc1nq1nfR5YX"
FEISHU_USER_ID = "ou_cae48beff850b3c9d72c59f8454c9439"
feishu_token = None

# 多语言支持
LANG = {"current": "zh"}
I18N = {
    "zh": {
        "title": "Gateway 监控",
        "status": "状态",
        "online": "在线",
        "offline": "离线",
        "unknown": "未知",
        "last_check": "最后检查",
        "start": "开始监控",
        "stop": "停止监控",
        "restart": "重启Gateway",
        "check": "手动检查",
        "settings": "设置",
        "interval": "检查间隔(秒)",
        "auto_restart": "自动重启",
        "language": "语言",
        "logs": "日志",
        "restarted": "Gateway 已重启上线！",
        "offline_alert": "Gateway 离线！",
    },
    "en": {
        "title": "Gateway Monitor",
        "status": "Status",
        "online": "Online",
        "offline": "Offline", 
        "unknown": "Unknown",
        "last_check": "Last Check",
        "start": "Start",
        "stop": "Stop",
        "restart": "Restart Gateway",
        "check": "Check Now",
        "settings": "Settings",
        "interval": "Interval (sec)",
        "auto_restart": "Auto Restart",
        "language": "Language",
        "logs": "Logs",
        "restarted": "Gateway Restarted!",
        "offline_alert": "Gateway Offline!",
    },
    "ja": {
        "title": "Gateway 監視",
        "status": "ステータス",
        "online": "オンライン",
        "offline": "オフライン",
        "unknown": "不明",
        "last_check": "最終確認",
        "start": "監視開始",
        "stop": "監視停止",
        "restart": "Gateway再起動",
        "check": "今すぐ確認",
        "settings": "設定",
        "interval": "確認間隔(秒)",
        "auto_restart": "自動再起動",
        "language": "言語",
        "logs": "ログ",
        "restarted": "Gateway再起動しました！",
        "offline_alert": "Gatewayオフライン！",
    }
}

def t(key):
    return I18N[LANG["current"]].get(key, key)

def get_feishu_token():
    global feishu_token
    try:
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        data = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
        r = requests.post(url, json=data, timeout=10)
        result = r.json()
        if result.get("code") == 0:
            feishu_token = result["tenant_access_token"]
            return True
    except:
        pass
    return False

def send_feishu(msg):
    global feishu_token
    if not feishu_token:
        get_feishu_token()
    try:
        url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
        headers = {"Authorization": f"Bearer {feishu_token}", "Content-Type": "application/json"}
        data = {"receive_id": FEISHU_USER_ID, "msg_type": "text", "content": json.dumps({"text": msg})}
        requests.post(url, headers=headers, json=data, timeout=10)
    except:
        pass
import winsound

# 配置
DEFAULT_PORT = 18789
DEFAULT_INTERVAL = 30  # 默认检查间隔（秒）
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gateway_monitor_config.json')
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gateway_monitor.lock')

# 单例检查
def check_single_instance():
    import os
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            # 检查进程是否在运行
            result = subprocess.run(f'tasklist /FI "PID eq {pid}"', capture_output=True, text=True, shell=True)
            if str(pid) in result.stdout:
                return False  # 已有实例在运行
        except:
            pass
    # 写入当前进程PID
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True

# 全局变量
status = "未知"
last_check_time = None
history_logs = []
is_monitoring = True  # 监控开关
check_thread = None
auto_restart = True
check_interval = DEFAULT_INTERVAL
root = None
icon = None


def load_config():
    """加载配置"""
    global check_interval, auto_restart
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                check_interval = config.get('check_interval', DEFAULT_INTERVAL)
                auto_restart = config.get('auto_restart', False)
    except Exception as e:
        print(f"加载配置失败: {e}")


def save_config():
    """保存配置"""
    try:
        config = {
            'check_interval': check_interval,
            'auto_restart': auto_restart
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存配置失败: {e}")


def check_gateway_status():
    """检查 Gateway 状态"""
    url = f"http://127.0.0.1:{DEFAULT_PORT}/"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True, "在线"
        else:
            return False, f"离线 (HTTP {response.status_code})"
    except requests.exceptions.ConnectionError:
        return False, "离线 (连接失败)"
    except requests.exceptions.Timeout:
        return False, "离线 (超时)"
    except Exception as e:
        return False, f"离线 ({str(e)})"


def restart_gateway():
    """重启 Gateway"""
    try:
        # 先杀掉 node 进程
        subprocess.run('taskkill /F /IM node.exe', 
                      shell=True, capture_output=True, timeout=30)
        time.sleep(1)
        # 再启动 - 开新窗口运行
        subprocess.Popen('cmd /k "openclaw gateway run --port 18789"',
                      shell=True)
        return True
    except Exception as e:
        return False


def add_log(message):
    """添加日志"""
    global history_logs
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    history_logs.insert(0, log_entry)
    if len(history_logs) > 30:
        history_logs = history_logs[:30]
    return log_entry


def check_status_loop():
    """状态检查循环"""
    global status, last_check_time, is_monitoring, check_interval, auto_restart
    
    while True:
        if is_monitoring:
            old_status = status
            is_online, status_msg = check_gateway_status()
            
            if is_online:
                status = "在线"
            else:
                status = "离线"
            
            last_check_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            add_log(f"Gateway {status_msg}")
            
            # 状态变化告警
            if old_status != "未知" and old_status != status:
                # 播放提示音
                try:
                    winsound.MessageBeep(winsound.MB_ICONWARNING)
                except:
                    pass
                
                # 托盘告警
                if icon:
                    show_notification(f"Gateway 状态变化: {old_status} → {status}")
                
                # 自动重启
                if auto_restart and status == "离线":
                    add_log("正在尝试自动重启 Gateway...")
                    if restart_gateway():
                        add_log("Gateway 重启命令已发送")
                        # 发送飞书通知
                        send_feishu("🦞 Gateway 已重启上线！")
                    else:
                        add_log("Gateway 重启失败")
            
            # 更新UI
            if root:
                root.after(0, update_ui)
        
        # 等待下次检查
        for _ in range(check_interval):
            if not is_monitoring:
                break
            time.sleep(0.5)


def update_ui_text():
    """更新UI文本（多语言）"""
    if not root or not root.winfo_exists():
        return
    try:
        root.title(t("title"))
    except:
        pass


def update_ui():
    """更新UI"""
    global root
    
    if not root or not root.winfo_exists():
        return
    
    # 更新文本
    update_ui_text()
    
    try:
        # 更新状态标签
        if status == "在线":
            root.status_label.config(text="● " + t("online"), fg="#28a745", font=("微软雅黑", 20, "bold"))
            root.status_indicator.config(bg="#28a745")
        else:
            root.status_label.config(text="● " + t("offline"), fg="#dc3545", font=("微软雅黑", 20, "bold"))
            root.status_indicator.config(bg="#dc3545")
        
        # 更新时间
        if last_check_time:
            root.last_check_label.config(text=f"最后检查: {last_check_time}")
        
        # 更新监控状态
        if is_monitoring:
            root.monitor_status_label.config(text="监控中", fg="#28a745")
            root.start_stop_btn.config(text="停止监控", bg="#dc3545", fg="white")
        else:
            root.monitor_status_label.config(text="已停止", fg="#6c757d")
            root.start_stop_btn.config(text="开始监控", bg="#28a745", fg="white")
        
        # 更新日志
        log_text = "\n".join(history_logs)
        root.log_text.delete(1.0, tk.END)
        root.log_text.insert(1.0, log_text)
    except:
        pass


def create_tray_icon(is_online=True):
    """创建托盘图标"""
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    if is_online:
        # 绿色 - 在线
        draw.ellipse([8, 8, 56, 56], fill='#28a745', outline='white', width=2)
        # 画一个勾
        draw.line([20, 32, 28, 42], fill='white', width=3)
        draw.line([28, 42, 44, 22], fill='white', width=3)
    else:
        # 红色 - 离线
        draw.ellipse([8, 8, 56, 56], fill='#dc3545', outline='white', width=2)
        # 画一个X
        draw.line([20, 20, 44, 44], fill='white', width=3)
        draw.line([44, 20, 20, 44], fill='white', width=3)
    
    return image


def show_notification(message):
    """显示通知"""
    if icon:
        try:
            icon.notify(message, "Gateway 监控")
        except:
            pass


def update_tray_icon():
    """更新托盘图标"""
    global icon
    if icon:
        try:
            is_online = (status == "在线")
            image = create_tray_icon(is_online)
            icon.icon = image
            icon.menu = pystray.Menu(
                pystray.MenuItem("显示主窗口", on_tray_show),
                pystray.MenuItem("手动检查", on_tray_check),
                pystray.MenuItem("重启 Gateway", on_tray_restart),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", on_tray_exit)
            )
        except:
            pass


def on_tray_show(icon, item):
    """托盘点击 - 显示"""
    global root
    if root:
        root.deiconify()
        root.lift()
        root.focus()


def on_tray_check(icon, item):
    """托盘点击 - 手动检查"""
    is_online, msg = check_gateway_status()
    status_str = "在线" if is_online else "离线"
    add_log(f"[托盘] 手动检查: Gateway {msg}")
    update_ui()
    update_tray_icon()


def on_tray_restart(icon, item):
    """托盘点击 - 重启"""
    add_log("[托盘] 正在重启 Gateway...")
    if restart_gateway():
        add_log("[托盘] 重启命令已发送")
    else:
        add_log("[托盘] 重启失败")
    update_ui()


def on_tray_exit(icon, item):
    """托盘点击 - 退出"""
    global is_monitoring
    is_monitoring = False
    if icon:
        icon.stop()
    if root:
        root.destroy()
    sys.exit(0)


def setup_tray():
    """设置托盘"""
    global icon
    
    image = create_tray_icon()
    
    menu = pystray.Menu(
        pystray.MenuItem("显示主窗口", on_tray_show),
        pystray.MenuItem("手动检查", on_tray_check),
        pystray.MenuItem("重启 Gateway", on_tray_restart),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", on_tray_exit)
    )
    
    icon = pystray.Icon("Gateway Monitor", image, "Gateway 监控", menu)
    icon.run_detached()


def on_closing():
    """窗口关闭事件 - 最小化到托盘"""
    global root
    root.withdraw()


def toggle_monitoring():
    """切换监控状态"""
    global is_monitoring
    is_monitoring = not is_monitoring
    
    if is_monitoring:
        add_log("监控已启动")
    else:
        add_log("监控已停止")
    
    update_ui()


def start_check_thread():
    """启动检查线程"""
    global check_thread
    check_thread = threading.Thread(target=check_status_loop, daemon=True)
    check_thread.start()


def main():
    """主函数"""
    global root, check_interval
    
    # 单例检查
    if not check_single_instance():
        print("监控程序已在运行！")
        try:
            root_temp = tk.Tk()
            root_temp.withdraw()
            tk.messagebox.showwarning("警告", "监控程序已在运行！")
        except:
            pass
        sys.exit(0)
    
    # 加载配置
    load_config()
    
    # 创建主窗口
    root = tk.Tk()
    root.title("Gateway 监控程序")
    root.geometry("480x650")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 主背景
    main_frame = tk.Frame(root, bg="#f5f5f5")
    main_frame.pack(fill="both", expand=True)
    
    # ===== 标题区域 =====
    title_frame = tk.Frame(main_frame, bg="#2196F3", height=60)
    title_frame.pack(fill="x")
    title_frame.pack_propagate(False)
    
    title_label = tk.Label(title_frame, text="🔌 Gateway 状态监控", 
                          font=("微软雅黑", 16, "bold"), fg="white", bg="#2196F3")
    title_label.pack(pady=15)
    
    # ===== 状态显示面板 =====
    status_panel = tk.Frame(main_frame, bg="white", bd=1, relief=tk.RIDGE)
    status_panel.pack(pady=15, padx=20, fill="x")
    
    # 状态指示灯
    root.status_indicator = tk.Canvas(status_panel, width=20, height=20, bg="white", highlightthickness=0)
    root.status_indicator.create_oval(2, 2, 18, 18, fill="#6c757d", outline="#6c757d")
    root.status_indicator.pack(side="left", padx=(15, 5), pady=15)
    
    # 状态文字
    status_text_frame = tk.Frame(status_panel, bg="white")
    status_text_frame.pack(side="left", fill="x", expand=True)
    
    root.status_label = tk.Label(status_text_frame, text="● 未知", 
                                 fg="#6c757d", font=("微软雅黑", 20, "bold"),
                                 bg="white")
    root.status_label.pack(anchor="w")
    
    root.last_check_label = tk.Label(status_text_frame, text="等待检查...", 
                                     font=("微软雅黑", 9), fg="#6c757d", bg="white")
    root.last_check_label.pack(anchor="w")
    
    root.monitor_status_label = tk.Label(status_panel, text="监控中", 
                                        font=("微软雅黑", 9, "bold"), 
                                        fg="#28a745", bg="white")
    root.monitor_status_label.pack(side="right", padx=15)
    
    # ===== 控制按钮区域 =====
    control_frame = tk.Frame(main_frame, bg="#f5f5f5")
    control_frame.pack(pady=5, padx=20, fill="x")
    
    def manual_check():
        is_online, msg = check_gateway_status()
        status_str = "在线" if is_online else "离线"
        add_log(f"手动检查: Gateway {msg}")
        update_ui()
        update_tray_icon()
    
    def manual_restart():
        if messagebox.askyesno("确认", "确定要重启 Gateway 吗?"):
            add_log("正在手动重启 Gateway...")
            if restart_gateway():
                add_log("重启命令已发送")
            else:
                add_log("重启失败")
            update_ui()
    
    # 启动/停止按钮
    root.start_stop_btn = tk.Button(control_frame, text="停止监控", 
                                    command=toggle_monitoring,
                                    font=("微软雅黑", 10, "bold"),
                                    bg="#dc3545", fg="white",
                                    width=12, height=1,
                                    relief=tk.RAISED)
    root.start_stop_btn.pack(side="left", padx=5)
    
    tk.Button(control_frame, text="手动检查", command=manual_check, 
              font=("微软雅黑", 10),
              width=10, height=1).pack(side="left", padx=5)
    
    tk.Button(control_frame, text="重启 Gateway", command=manual_restart,
              font=("微软雅黑", 10),
              width=12, height=1).pack(side="left", padx=5)
    
    # ===== 设置界面 =====
    settings_frame = tk.LabelFrame(main_frame, text="⚙️ 设置", font=("微软雅黑", 11, "bold"),
                                   bg="#f5f5f5", fg="#333")
    settings_frame.pack(pady=10, padx=20, fill="x")
    
    # 检查间隔设置
    interval_frame = tk.Frame(settings_frame, bg="#f5f5f5")
    interval_frame.pack(pady=8, fill="x", padx=10)
    
    tk.Label(interval_frame, text="检查间隔 (秒):", font=("微软雅黑", 10),
             bg="#f5f5f5").pack(side="left")
    
    interval_var = tk.StringVar(value=str(check_interval))
    interval_spin = tk.Spinbox(interval_frame, from_=5, to=300, 
                               textvariable=interval_var, width=8,
                               font=("微软雅黑", 10))
    interval_spin.pack(side="left", padx=10)
    
    def update_interval():
        global check_interval
        try:
            new_interval = int(interval_var.get())
            if new_interval >= 5:
                check_interval = new_interval
                save_config()
                add_log(f"检查间隔已设置为 {new_interval} 秒")
        except:
            pass
    
    tk.Button(interval_frame, text="应用", command=update_interval,
              font=("微软雅黑", 9), width=6).pack(side="left")
    
    # 自动重启开关
    auto_restart_frame = tk.Frame(settings_frame, bg="#f5f5f5")
    auto_restart_frame.pack(pady=5, fill="x", padx=10)
    
    auto_restart_var = tk.BooleanVar(value=auto_restart)
    
    def toggle_auto_restart():
        global auto_restart
        auto_restart = auto_restart_var.get()
        save_config()
        status = "开启" if auto_restart else "关闭"
        add_log(f"自动重启已{status}")
    
    auto_restart_check = tk.Checkbutton(auto_restart_frame, 
                                        text="Gateway 离线时自动重启",
                                        variable=auto_restart_var,
                                        command=toggle_auto_restart,
                                        font=("微软雅黑", 10),
                                        bg="#f5f5f5",
                                        activebackground="#f5f5f5")
    auto_restart_check.pack(side="left")
    
    # 语言选择
    lang_frame = tk.Frame(settings_frame, bg="#f5f5f5")
    lang_frame.pack(pady=5, fill="x", padx=10)
    
    tk.Label(lang_frame, text="语言/Language/言語:", font=("微软雅黑", 10),
             bg="#f5f5f5").pack(side="left")
    
    lang_var = tk.StringVar(value=LANG["current"])
    
    def change_lang(*args):
        LANG["current"] = lang_var.get()
        add_log(f"语言已切换: {lang_var.get()}")
        update_ui_text()
    
    lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var, 
                              values=["zh", "en", "ja"], width=5,
                              state="readonly")
    lang_combo.pack(side="left", padx=10)
    lang_combo.bind("<<ComboboxSelected>>", change_lang)
    
    # ===== 日志区域 =====
    log_frame = tk.LabelFrame(main_frame, text="📋 监控日志", font=("微软雅黑", 11, "bold"),
                             bg="#f5f5f5", fg="#333")
    log_frame.pack(pady=10, padx=20, fill="both", expand=True)
    
    # 日志文本框（带滚动条）
    log_scroll = tk.Scrollbar(log_frame)
    log_scroll.pack(side="right", fill="y")
    
    root.log_text = tk.Text(log_frame, height=10, font=("Consolas", 9),
                            yscrollcommand=log_scroll.set,
                            bg="#1e1e1e", fg="#00ff00", insertbackground="white")
    root.log_text.pack(padx=(10,0), pady=10, fill="both", expand=True)
    log_scroll.config(command=root.log_text.yview)
    
    # ===== 状态栏 =====
    status_bar = tk.Label(main_frame, text="程序运行中 | 双击托盘图标显示主窗口",
                         bd=1, relief=tk.SUNKEN, anchor=tk.W,
                         font=("微软雅黑", 8), bg="#e9ecef")
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # 初始日志
    add_log("Gateway 监控程序已启动")
    add_log(f"检查间隔: {check_interval} 秒")
    add_log(f"自动重启: {'开启' if auto_restart else '关闭'}")
    
    # 启动托盘
    try:
        setup_tray()
        add_log("系统托盘已启动")
    except Exception as e:
        print(f"托盘启动失败: {e}")
        add_log(f"托盘启动失败: {e}")
    
    # 启动检查线程
    start_check_thread()
    
    # 立即进行一次检查
    root.after(500, lambda: [update_ui(), update_tray_icon()])
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    # 检查依赖
    try:
        import requests
    except ImportError:
        print("请安装 requests 库: pip install requests")
        input("按回车键退出...")
        sys.exit(1)
    
    try:
        import pystray
    except ImportError:
        print("请安装 pystray 库: pip install pystray")
        input("按回车键退出...")
        sys.exit(1)
    
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("请安装 Pillow 库: pip install Pillow")
        input("按回车键退出...")
        sys.exit(1)
    
    main()
