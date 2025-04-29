# 新增：翻译字典
translations = {
    "en": {
        # info logger information
        "vpn_start_running": "\033[2J\033[H\033[32m[VPNGATE-CLIENT] for Windows, Start running...\033[0m",
        "vpnlist_expired": "\033[33mVPN servers list expired,download now!\033[0m",
        "download_from_main_url": "Downloading VPN list from \033[90;4m%s\033[0m",
        "vpnlist_download_saved_to_file": "VPN list downloaded and saved to \033[90;4m%s\033[0m",
        "failed_to_download_from_main_url": "\033[31mMain URL is unavailable, switch to backup URL!\033[0m",
        "proxy_check_failed": "Proxy check failed for \033[4m%s\033[0m",
        "available_GitHub_proxy": "\033[32mFound available GitHub proxy: \033[4m%s\033[0m",
        "fallback_to_original_url": "No available proxy found, using original URL: \033[90;4m%s\033[0m",
        "attempt_download_from_backup_url": "Attempting to download from backup URL: \033[90;4m%s\033[0m",
        "failed_to_download_from_backup_url": "Failed to download from backup URL too: \033[90;4m%s\033[0m",
        "file_path_not_found": "File path not found: \033[90;4m%s\033[0m",
        "get_vpnlist_with_backup_proxy": "Get VPN list with backup proxy: \033[90;4m%s\033[0m",
        "loading_vpn_list": "Loading VPN list from \033[90;4m%s\033[0m",
        "found_vpn_servers": "Found \033[32m%i\033[0m VPN servers",
        "filtering_servers": "Filtering out unresponsive VPN servers",
        "found_responding_vpns": "Found \033[32m%i\033[0m responding VPNs",
        "vpn_init_success": "VPN initialized successfully! Country: %s",
        "setup_iptables_rules": "Setting iptables rules to block non-VPN traffic",
        "clear_ptables_rules": "Clearing iptables rules",
        "bad_download_speed": "\033[33mBad download speed,attempting next server...\033[0m",
        "error_download_speed": "\033[33mdownload speed test failed,attempting next server...\033[0m",
        "next_vpn": "Next VPN...",
        "performing_speedtest": "\033[90mPerforming connection speed test. Press CTRL+C to stop it.\033[0m",
        "speedtest_canceled": "Speedtest Canceled!",
        "use_or_change": "Would you like to use this VPN ? (No = \033[1mCTRL+C\033[0m, Yes = Any Key)",
        "setup_finished": "\033[32mSetup finished!\033[0m \033[90m(Press CTRL+C to stop the VPN)\033[0m",
        "connection_disconnected": "\033[33m\nVPN monitor found connection disconnected, Attempting to connect next server!\033[0m",
        "connection_closed": "\033[90mip %s port %s country %s,connection closed!\033[0m",
        "connecting_to_vpn": "Connecting to VPN...",
        "writing_config": "Writing config to %s",
        "executing_cmd": "Executing %s",
        "vpn_init_failed": "VPN initialization failed.",
        "vpn_init_timeout": "VPN Initialization timed out.",
        "received_keyboard_interrupt": "\033[31mReceived keyboard interrupt.\033[0m",
        "terminating_vpn": "Terminating VPN connection",
        "vpn_terminated": "VPN connection Terminated!",
        "termination_timeout": "Termination timed out. Killing the process.",
        "vpn_unkillable": "The VPN process can't be killed!",
        "delete_tmp_dir": "The temporary folder has been deleted",
        "delete_tmp_dir_failed": "Temporary folder deletion failed",
        "exiting": "\033[31mExiting...\033[0m",
        # debug输出
        "probing_vpn": "Probing VPN endpoint",
        "cant_probe_udp": "Can't probe UDP servers",
        "vpn_not_responding": "VPN endpoint did not respond to connection",
        "connection_failed": "Connection failed",
        "vpn_listening": "VPN endpoint is listening",
        # help info
        "appDescription": "Client for vpngate.net VPNs",
        "positional_arguments": "positional arguments",
        "optional_arguments": "options",
        "h_help": "show this help message and exit",
        "h_arg_country": "A 2 char country code (e.g. CA for Canada) from which to look for VPNs. If specified multiple times, VPNs from all the countries will be selected.",
        "h_arg_eu": "Adds European countries to the list of considerable countries.",
        "h_arg_probes": "Number of concurrent connection probes to send.",
        "h_arg_iptables": "Setting iptables rules to block non-VPN traffic",
        "h_arg_probe_timeout": "When probing, how long to wait for connection until marking the VPN as unavailable (seconds).",
        "h_arg_url": "URL of the VPN list (csv).",
        "h_arg_us": "Adds United States to the list of possible countries. Shorthand or --country US.",
        "h_arg_verbose": "More verbose output.",
        "h_arg_vpn_timeout": "Time to wait for a VPN to be established before giving up (seconds).",
        "h_arg_vpn_timeout_poll_interval": "Time between two checks for a potential timeout (seconds).",
        "h_arg_ovpnfile": "Connects to the OpenVPN VPN whose configuration is in the provided .ovpn file.",
        "h_arg_expired_time": "Time to wait for a ServersList to be expired.",
        "h_arg_min_speed": "Minimum download speed.",
    },
    "zh": {
        # info
        "vpn_start_running": "\033[2J\033[H\033[32m[VPNGATE-CLIENT] VPNGATE Windows 客户端, 开始运行...\033[0m",
        "vpnlist_expired": "\033[33mVPN 服务器列表已过期，重新下载!\033[0m",
        "download_from_main_url": "从 \033[90;4m%s\033[0m 下载 VPN 服务器列表",
        "vpnlist_download_saved_to_file": "VPN 服务器列表已下载并保存到 \033[90;4m%s\033[0m",
        "failed_to_download_from_main_url": "\033[31m主下载网址不可用，切换备用网址！\033[0m",
        "proxy_check_failed": "GitHub 代理地址 \033[4m%s\033[0m 暂不可用！",
        "available_GitHub_proxy": "\033[32m发现可用GitHub 代理: \033[4m%s\033[0m",
        "fallback_to_original_url": "没有可用GitHub代理，使用原始网址: \033[90;4m%s\033[0m",
        "attempt_download_from_backup_url": "尝试从备用网址下载: \033[90;4m%s\033[0m",
        "failed_to_download_from_backup_url": "从备用地址 \033[90;4m%s\033[0m 也下载失败了！",
        "file_path_not_found": "文件路径不存在: \033[90;4m%s\033[0m",
        "get_vpnlist_with_backup_proxy": "使用备用代理获取 VPN 服务器列表: \033[90;4m%s\033[0m",
        "loading_vpn_list": "从文件 \033[90;4m%s\033[0m 加载VPN服务器列表",
        "found_vpn_servers": "总共 \033[32m%i\033[0m 个 VPN 服务器",
        "filtering_servers": "过滤无响应服务器",
        "found_responding_vpns": "发现 \033[32m%i\033[0m 个可用 VPN 服务器",
        "vpn_init_success": "VPN初始化成功！国家：%s",
        "setup_iptables_rules": "设置 iptables 规则以阻止非 VPN 流量",
        "clear_ptables_rules": "清除 iptables 规则",
        "performing_speedtest": "\033[90m运行 VPN 连接速度测试，按 CTRL+C 终止测速.\033[0m",
        "speedtest_canceled": "下载速度测试取消!",
        "bad_download_speed": "下载速度不佳，尝试下一个服务器...",
        "error_download_speed": "下载速度检测出错，尝试下一个服务器...",
        "next_vpn": "下一个VPN...",
        "use_or_change": "是否使用此 VPN ? ( 按任意键确认！ 按 \033[1mCTRL+C\033[0m 切换VPN！)",
        "setup_finished": "\033[32mVPN 链接设置完成!\033[0m \033[90m(按 CTRL+C 结束连接并退出)\033[0m",
        "connection_disconnected": "\nVPN监测程序发现连接已断开，尝试下一个服务器！",
        "connection_closed": "IP %s 端口 %s 国家 %s，连接已关闭！",
        "connecting_to_vpn": "正在连接VPN...",
        "writing_config": "正在将配置写入 %s",
        "executing_cmd": "执行命令 %s",
        "vpn_init_failed": "VPN初始化失败。",
        "vpn_init_timeout": "VPN初始化超时。",
        "received_keyboard_interrupt": "收到键盘中断。",
        "terminating_vpn": "正在终止VPN连接",
        "vpn_terminated": "VPN连接已终止！",
        "termination_timeout": "终止超时。正在强制结束进程。",
        "vpn_unkillable": "无法终止VPN进程！",
        "delete_tmp_dir": "临时文件夹已删除",
        "delete_tmp_dir_failed": "临时文件夹删除失败",
        "exiting": "\033[31m退出程序...\033[0m",
        # debug
        "probing_vpn": "正在探测VPN端点",
        "cant_probe_udp": "无法探测UDP服务器",
        "vpn_not_responding": "VPN端点未响应连接",
        "connection_failed": "连接失败",
        "vpn_listening": "VPN端点正在监听",
        # 帮助信息
        "appDescription": "vpngate.net 的VPN客户端",
        # 'appUsage': '用法: vpngateclientcn.py [选项] [ovpnfile]',
        "positional_arguments": "位置参数",
        "optional_arguments": "可选参数",
        "h_help": "显示此帮助信息并退出",
        "h_arg_country": "指定一个两位字母的国家代码（例如 CA 代表加拿大），用于选择 VPN。可多次指定多个国家的 VPN。",
        "h_arg_eu": "将欧洲国家添加到可考虑的国家列表中。",
        "h_arg_probes": "发送的并发连接探测数量。",
        "h_arg_iptables": "设置 iptables 规则以阻止非 VPN 流量",
        "h_arg_probe_timeout": "探测时，等待连接的时间，超时后标记该 VPN 为不可用（以秒为单位）。",
        "h_arg_url": "VPN 列表的 URL（csv）。",
        "h_arg_us": "将美国添加到可能的国家列表中。简写为 --country US。",
        "h_arg_verbose": "输出更多详细信息。",
        "h_arg_vpn_timeout": "等待 VPN 建立连接的时间，超时后放弃（以秒为单位）。",
        "h_arg_vpn_timeout_poll_interval": "两次检查潜在超时的时间间隔（以秒为单位）。",
        "h_arg_ovpnfile": "连接到 OpenVPN 的 VPN，其配置文件为提供的 .ovpn 文件。",
        "h_arg_expired_time": "等待服务器列表过期的时间。",
        "h_arg_min_speed": "最低下载速度。",
    },
}


# 获取翻译文本的函数
def get_text(key, lang=None):
    import locale
    import warnings

    # 忽略 locale.getdefaultlocale() 的弃用警告
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning, message=".*getdefaultlocale.*"
    )

    def get_system_language():
        try:
            return locale.getdefaultlocale()[0]
        except Exception:
            return "en_US"

    if lang is None:
        lang = get_system_language()[:2]
    return translations.get(lang, translations["en"]).get(key, translations["en"][key])
