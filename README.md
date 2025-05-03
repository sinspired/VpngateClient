# VpngateClient

A client for connecting to [vpngate.net](http://vpngate.net) OpenVPN servers.

[![Release Version](https://img.shields.io/github/v/release/sinspired/VpngateClient?display_name=tag&logo=github&label=Release)](https://github.com/sinspired/VpngateClient/releases/latest)
[![GitHub repo size](https://img.shields.io/github/repo-size/sinspired/VpngateClient?logo=github)
](https://github.com/sinspired/VpngateClient)
[![GitHub last commit](https://img.shields.io/github/last-commit/sinspired/VpngateClient?logo=github&label=最后提交：)](https://github.com/sinspired/VpngateClient)

## Features

- Filter VPN servers by geographical location (country or Europe)
- Probe VPN endpoints to skip unresponsive servers before connecting
- Perform a speed test after connecting, so you can decide to keep or try the next server
- If a server running stable for 5 minutues, save it in a qualified lists

## Dependencies

- [Python](https://python.org) (>= 3.3)
- [OpenVPN](https://openvpn.net/)

---

## Usage

> [!NOTE]
> You must run as Administrator (Windows) or with `sudo` (Linux) to allow OpenVPN to work properly.

For all options, run: `vpngate --help`

### 🐧 Install for Linux

```bash
git clone https://github.com/sinspired/VpngateClient.git
cd VpngateClient
sudo pip install -e .
sudo vpngate
```

### 🪟 Install for Windows

Open **PowerShell** or **CMD** as Administrator, then:

```powershell
git clone https://github.com/sinspired/VpngateClient.git
cd VpngateClient
pip install -e .
vpngate
```

### 🛠️ Install for Development

If you are using a system-managed Python environment (e.g., on Ubuntu), you may encounter restrictions when installing packages system-wide. To install in development mode, use:

```bash
sudo pip install -e . --break-system-packages
```

> **Warning:** Using `--break-system-packages` may affect your system's Python environment.  
> For a safer approach, consider using a virtual environment.

---

### 🚀 Simple Usage

Try VPN servers one-by-one, default sorted by score, or sorted by latency( `-s` ):

```bash
chmod +x ./VpngateClient/VpngateClient.py
sudo ./VpngateClient/VpngateClient.py  # -s to sort by latency
```

---

### 🌎 Filter by Country

Only consider VPN servers in a specific country (e.g., Canada):

```bash
sudo ./VpngateClient/VpngateClient.py --country CA  # -c CA
sudo ./VpngateClient/VpngateClient.py --us  # --us is a shorthand for --country US
```

The country identifier is a 2-letter code (ISO 3166-1 alpha-2).

---

### 🇪🇺 VPNs in Europe

Only consider VPN servers in Europe:

```bash
sudo ./VpngateClient/VpngateClient.py --eu
```

---

### 📝 Other Options

See all command line options:

```bash
sudo vpngate --help
```
