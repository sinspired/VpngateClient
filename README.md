# VpngateClient

[![Release Version](https://img.shields.io/github/v/release/sinspired/VpngateClient?display_name=tag&logo=github&label=Release)](https://github.com/sinspired/VpngateClient/releases/latest)
[![GitHub last commit](https://img.shields.io/github/last-commit/sinspired/VpngateClient?logo=github&label=最后提交：)](https://github.com/sinspired/VpngateClient)

A client for connecting to [vpngate.net](http://vpngate.net) OpenVPN servers.

## Features

- Filter VPN servers by geographical location (country, Europe, or USA)
- Probe VPN endpoints to skip unresponsive servers before connecting
- Perform a speed test after connecting, so you can decide to keep or try the next server
- If a server runs stable for 5 minutes, save it in a qualified list for priority use
- Support for both Linux and Windows (with color output)
- Automatically sorts servers by latency (can be disabled)
- Supports connecting with your own `.ovpn` config file

## Dependencies

- [Python](https://python.org) (>= 3.7 recommended)
- [OpenVPN](https://openvpn.net/) (must be installed and in PATH)

> On Linux, you may need `sudo` to install system-wide or use a virtual environment.

## Usage

> [!NOTE]
> You must run as Administrator (Windows) or with `sudo` (Linux) to allow OpenVPN to work properly.

For all options, run:

```bash
python3 ./VpngateClient/VpngateClient.py --help
```

### 🐧 Install for Linux

```bash
git clone https://github.com/sinspired/VpngateClient.git
cd VpngateClient
sudo pip install -e .
sudo python3 ./VpngateClient/VpngateClient.py
```

### 🪟 Install for Windows

Open **PowerShell** or **CMD** as Administrator, then:

```powershell
git clone https://github.com/sinspired/VpngateClient.git
cd VpngateClient
pip install -e .
py VpngateClient\VpngateClient.py
```

> [!NOTE]
> If you see color output issues, run `pip install colorama` or `pip install -r requirements.txt`.

### 🛠️ Install for Development

If you are using a system-managed Python environment (e.g., on Ubuntu), you may encounter restrictions when installing packages system-wide. To install in development mode, use:

```bash
sudo pip install -e . --break-system-packages
```
> [!WARNING]
> Using `--break-system-packages` may affect your system's Python environment.  
> For a safer approach, consider using a virtual environment.

### 🚀 Simple Usage

Try VPN servers one-by-one, default sorted by latency (lowest first):

```bash
sudo python3 ./VpngateClient/VpngateClient.py
```

To disable latency sorting (use original order):

```bash
sudo python3 ./VpngateClient/VpngateClient.py  # --no-sort-latency to cancel sort by latency
```

### 🌎 Filter by Country

Only consider VPN servers in a specific country (e.g., Canada):

```bash
sudo python3 ./VpngateClient/VpngateClient.py --country CA  # -c CA
sudo python3 ./VpngateClient/VpngateClient.py --us          # --us is a shorthand for --country US
```

The country identifier is a 2-letter code (ISO 3166-1 alpha-2).

### 🇪🇺 VPNs in Europe

Only consider VPN servers in Europe:

```bash
sudo python3 ./VpngateClient/VpngateClient.py --eu
```

### 🔗 Connect with Your Own .ovpn File

You can connect directly using your own OpenVPN config file:

```bash
sudo python3 ./VpngateClient/VpngateClient.py /path/to/your.ovpn
```

### 📝 Other Options

See all command line options:

```bash
python3 ./VpngateClient/VpngateClient.py --help
```

## 常见问题（FAQ）

- **Q: 提示找不到 openvpn 命令？**  
  A: 请先安装 OpenVPN，并确保其在系统 PATH 路径下。Linux 可用 `sudo apt install openvpn`，Windows 请从官网下载安装。

- **Q: 权限不足或无法连接？**  
  A: 请用 `sudo`（Linux）或以管理员身份运行（Windows）。

- **Q: 依赖 colorama 报错？**  
  A: Windows 下请运行 `pip install colorama` 或 `pip install -r requirements.txt`。

- **Q: 如何收藏优质节点？**  
  A: 连接稳定超过 5 分钟的节点会自动保存，下次优先尝试。

- **Q: 如何只测速不连接？**  
  A: 目前不支持单独测速，连接后会自动测速。

## 简要说明（中文）

- 本工具自动下载并筛选 vpngate 免费节点，优先连接响应快、速度高的服务器。
- 支持国家/地区过滤、测速、自动收藏优质节点。
- 支持自定义 .ovpn 文件一键连接。
- 需确保 Python3、OpenVPN 已安装，运行时需管理员权限。
