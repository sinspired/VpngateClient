A client for connecting to [vpngate.net](http://vpngate.net) OpenVPN servers.

**Features**:

- filters VPN servers by their geographical location (country or VPNs in Europe)
- probes the VPN endpoints to detect ones that aren't responding for some reason
  before connecting to the VPN server
- once connected, performs a speed-test for the VPN and lets you decide if the
  speed is good enough for you or if you want to try the next one on the list

## Dependencies

This client has following dependencies:

- [python](https://python.org) (at least v3.3)
- [OpenVPN](https://openvpn.net/)

## Usage

### Install for Windows

```powershell
  git clone https://github.com/sinspired/VpngateClient.git
  cd VpngateClient
  pip install -e .
  vpngate
```

Note: `vpngate -h` for help

### Install for Development

If you are using a system-managed Python environment (e.g., on Ubuntu), you may encounter restrictions when installing packages system-wide. To install in development mode, you can use the following command:

```bash
pip install -e . --break-system-packages
```

**Warning**: Using `--break-system-packages` may affect your system's Python environment. If you prefer a safer approach, consider using a virtual environment.

### Simple Case

Note: `sudo` is required for OpenVPN.

```shell
  chmod +x ./VpngateClient/VpngateClient.py
  sudo ./VpngateClient/VpngateClient.py
````

This tries the VPN servers one-by-one ordered by their latency and asks you to
choose the one you like.

### Filter by Country

```shell
  sudo ./VpngateClient/VpngateClient.py --country CA
  sudo ./VpngateClient/VpngateClient.py --us # --us is a shorthand for --country US
```

The above command only considers VPN servers in Canada. The country identifier is a 2 digit code (ISO 3166-2).

### VPNs in Europe

```shell
  sudo ./VpngateClient/VpngateClient.py --eu
```

As a special case, the `--eu` flag only considers VPN servers in Europe.

### Other Options

All the command line options are available by running `vpngate --help`.
