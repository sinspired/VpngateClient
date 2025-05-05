#!/usr/bin/env python3
import argparse
import base64
import concurrent.futures
import csv
import ctypes
import logging
import os
import platform
import re
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta

# 本地模块导入
if __name__ == "__main__":
    # 绝对导入用于脚本运行
    from module_firewall import FirewallManager, IPv4_COMMANDS, IPv6_COMMANDS
    from module_translations import get_text
    from user_data_manager import UserDataManager
else:
    # 相对导入用于模块导入
    from .module_firewall import FirewallManager, IPv4_COMMANDS, IPv6_COMMANDS
    from .module_translations import get_text
    from .user_data_manager import UserDataManager

logger = logging.getLogger()

is_linux = platform.system() == "Linux"
is_windows = platform.system() == "Windows"

# The URL for the VPN list
VPN_LIST_URL = "https://www.vpngate.net/api/iphone/"
SPEED_TEST_URL = "http://ipv4.download.thinkbroadband.com/50MB.zip"
# SPEED_TEST_URL = "https://cachefly.cachefly.net/50mb.test"
LOCAL_CSV_NAME = "servers.csv"
DEFAULT_EXPIRED_TIME = 0.15
DEFAULT_MIN_SPEED = 0.00
SET_UDP_LATENCY = 60
DEFAULT_QUALIFIED_TIME = 5
DEFAULT_VPN_TIMEOUT = 9 if is_windows else 4

# The app running with temp\cahe\config DIRs,automatic with promission and exists
APP_RUNNING_DIR = UserDataManager("VpngateClient")

TEMP_DIR = APP_RUNNING_DIR.temp_dir
CACHE_DIR = APP_RUNNING_DIR.cache_dir
CONFIG_DIR = APP_RUNNING_DIR.config_dir

EU_COUNTRIES = [
    ["AL", "AT", "BA", "BE", "BG", "CH", "CY", "DE", "DK", "EE", "SI"],
    ["ES", "FI", "FR", "GB", "GR", "HR", "HU", "IE", "IS", "IT", "SE"],
    ["LT", "LV", "MK", "MT", "NL", "NO", "PL", "PT", "RO", "RS"],
]


class VPNClient:
    """A VPN Client Manager."""

    def __init__(self, data, args):
        # Command Line Arguments
        self.args = args

        # Logging
        if self.args.verbose:
            self.log = logging.getLogger(
                "%s %s"
                % (
                    self.__class__.__name__,
                    data.get("#HostName", data.get("IP", "Unknown")),
                )
            )  # Use get for safety
        else:
            self.log = logging.getLogger(self.__class__.__name__)  # 净化输出

        # VPN Information
        self.ip = data.get("IP")  # Use get for safety
        self.country = data.get("CountryLong", "Unknown")
        self.country_code = data.get("CountryShort", "??")

        # OpenVPN endpoint information
        self.proto = None
        self.port = None

        # OpenVPN Config
        conf = data.get("OpenVPN_ConfigData_Base64", "")
        if not conf:
            self.log.error("Missing OpenVPN config data.")
            raise ValueError("Missing OpenVPN config data.")  # Or handle appropriately
        try:
            self.config = base64.b64decode(conf).decode("UTF-8")
        except (base64.binascii.Error, UnicodeDecodeError) as e:
            self.log.error(f"Failed to decode Base64 config: {e}")
            raise ValueError(f"Invalid Base64 config: {e}") from e

        # Instance variable to track if saved as qualified
        self.saved_as_qualified = False
        # Instance variable to store the qualified config file path once determined
        self.qualified_vpn_config_path = None
        self.qualified_vpn_csv_path = None

        self.udp_latency = getattr(args, "udp_latency", SET_UDP_LATENCY)

        for line in self.config.splitlines():
            parts = line.split()
            if line.startswith("remote") and len(parts) == 3:
                # format: remote <ip> <port>
                _, remote_ip, remote_port_str = parts
                # If the IP was not provided or differs, log potentially useful info
                if not self.ip:
                    self.ip = remote_ip
                elif remote_ip != self.ip:
                    self.log.warning(
                        # 配置中的 remote IP 与提供的 IP 不一致，使用提供的 IP
                        f"Config remote IP '{remote_ip}' differs from provided IP '{self.ip}'. Using '{self.ip}'."
                    )
                # Validate and set port
                try:
                    self.port = int(remote_port_str)
                except ValueError:
                    self.log.warning(
                        # 配置中的端口无效，跳过该行
                        f"Invalid port '{remote_port_str}' in config. Skipping line."
                    )
                    continue

            elif line.startswith("proto") and len(parts) == 2:
                # format: proto tcp|udp
                _, self.proto = parts
                if self.proto not in ["tcp", "udp"]:
                    self.log.warning(
                        # 配置中的协议不支持，设为 None
                        f"Unsupported proto '{self.proto}' in config. Using 'None'."
                    )
                    self.proto = None  # Or default to one?

        # Ensure essential info was found
        if not self.ip or not self.port or not self.proto:
            self.log.error("Could not determine IP, Port, or Protocol from config.")
            # Decide how to handle this - maybe raise an error or mark as invalid
            # For now, let's log and potentially fail later
            # raise ValueError("Incomplete VPN endpoint information derived from config.")

        self.log.debug(
            # 新 VPN 信息
            "New VPN: ip=%s, proto=%s port=%s country=%s (%s)",
            self.ip,
            self.proto,
            self.port,
            self.country,
            self.country_code,
        )
        # Determine potential qualified file paths early
        if self.ip and self.port and self.proto:  # Check if we have needed info
            self.qualified_vpn_config_path = os.path.join(
                CONFIG_DIR,
                f"{self.country_code}_{self.ip}_{self.port}_{self.proto}.ovpn",
            )
            self.qualified_vpn_csv_path = os.path.join(CONFIG_DIR, "qualified_vpns.csv")

        # Initialize FirewallManager
        self.firewall = FirewallManager(self.ip, IPv4_COMMANDS, IPv6_COMMANDS)

    def is_listening(self):
        """Probes the VPN endpoint to see if it's listening and measures latency."""
        if not self.ip or not self.port:
            self.log.error("Cannot probe VPN without IP and Port.")
            return False, float("inf")  # Return infinite latency if invalid

        if self.proto == "udp":
            udp_latency = self.udp_latency
            self.log.debug(get_text("cant_probe_udp"), udp_latency)
            return True, float(
                udp_latency
            )  # UDP probing not implemented, return low latency, because UDP connect make better performance

        self.log.debug(get_text("probing_vpn"))

        # Create a socket with a timeout.
        s = socket.socket()
        s.settimeout(self.args.probe_timeout)

        try:
            # Measure start time
            start_time = time.time()

            # Try to connect to the VPN endpoint.
            s.connect((self.ip, int(self.port)))  # Ensure port is int
            s.shutdown(socket.SHUT_RDWR)

            # Measure end time and calculate latency
            latency = (time.time() - start_time) * 1000
            self.log.debug(get_text("vpn_listening"), f"{latency:.0f} ms")
            return True, latency
        except socket.timeout:
            self.log.debug(get_text("vpn_not_responding"))
            return False, float("inf")
        except (
            ConnectionRefusedError,
            OSError,
            socket.gaierror,
        ) as e:
            self.log.debug(f"{get_text('connection_failed')}: {e}")
            return False, float("inf")
        except Exception as e:
            self.log.exception(f"Unexpected error during probing: {e}")
            return False, float("inf")
        finally:
            s.close()  # Ensure socket is closed

    def connect(self):
        """Initiates and manages the connection to this VPN server.

        Returns:
            (boolean) True if the connection was established and used successfully
                      (until user interrupt or disconnect), False if the connection
                      failed, was rejected by the user, or had issues.

        Throws:
            (KeyboardInterrupt) if the process was aborted by the user during critical phases.
        """
        if not self.ip or not self.port or not self.proto:
            self.log.error("Cannot connect: Missing IP, Port, or Protocol.")
            return False

        self.log.info(get_text("connecting_to_vpn"))

        # --- Config File Setup ---
        config_file_path = os.path.join(
            TEMP_DIR, f"vpn_{self.ip}_{self.port}_{self.country_code}.ovpn"
        )

        try:
            with open(
                config_file_path, mode="w", encoding="utf-8"
            ) as conf_file:  # Use 'w' and specify encoding
                self.log.debug(get_text("writing_config") % conf_file.name)
                conf_file.write(self.config)
                # Add required options reliably
                conf_file.write("\ndata-ciphers AES-128-CBC\n")  # Ensure newline before
                conf_file.write("remote-cert-tls server\n")
                conf_file.write("disable-dco\n")
                # Ensure buffer is written
                conf_file.flush()
                # File closed automatically by 'with' statement

            # os.chmod(config_file_path, 0o777)
        except IOError as e:
            self.log.error(f"Failed to write config file {config_file_path}: {e}")
            return False
        # --- End Config File Setup --

        cmd, status_file_path = self.build_ovpn_command(config_file_path)
        self.log.debug(
            get_text("executing_cmd") % " ".join(cmd)
        )  # Join for better logging

        proc = None  # Initialize proc to None
        try:
            # --- Start OpenVPN Process ---
            proc = subprocess.Popen(
                cmd,
                start_new_session=True,  # Detach from parent (useful for backgrounding)
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr too
                universal_newlines=True,  # Decode output as text
                encoding="utf-8",  # Specify encoding
                errors="replace",  # Handle potential decoding errors
            )

            # --- Wait for VPN Initialization ---
            if not self.wait_for_vpn_ready(proc, config_file_path):
                # VPN failed to initialize. Error logged in wait_for_vpn_ready.
                # Terminate and cleanup are handled within wait_for_vpn_ready or its exception handlers
                # Need to ensure cleanup happens if wait_for_vpn_ready returns False normally
                self.log.debug("VPN process did not initialize correctly.")
                self.terminate_vpn(proc)  # Attempt termination if still running
                self._cleanup_temp_files(config_file_path, status_file_path)
                return False

            # if is_linux and os.path.exists(status_file_path):
            # os.chmod(status_file_path, 0o777)
            # os.chown(status_file_path, uid, gid)  # 修复所有权

            # --- Perform Speed Test ---
            speed_result = self.vpncheck()
            require_delayed_prompt = False

            if speed_result == "error":
                print(
                    get_text(
                        "Speedtest failed or returned error. Monitoring connection before prompting."
                    ),
                    end="\r",
                )
                # Proceed without immediate prompt, will prompt after 10s in monitor if stable
                require_delayed_prompt = True
                # Continue assuming user wants to try, relying on monitor + delayed prompt
            elif not speed_result:
                # Speed test returned False (bad speed)
                self.log.info(get_text("bad_download_speed") + " Terminating.")
                self.terminate_vpn(proc)
                self._cleanup_temp_files(config_file_path, status_file_path)
                return False
            else:
                # Speed test was successful (True)
                use_this_vpn = self.prompt_use_vpn()
                if not use_this_vpn:
                    print("\033[33m" + get_text("next_vpn") + "\033[0m")
                    self.terminate_vpn(proc)
                    self._cleanup_temp_files(config_file_path, status_file_path)
                    return False
                # User explicitly confirmed (or timed out positively)

            # --- Setup Firewall (if requested) ---
            if self.args.iptables and is_linux:
                self.log.info("Setting up Linux firewall rules.")
                if not self.setup_iptables_rules():
                    self.log.error(
                        "Failed to set up firewall rules. Terminating connection."
                    )
                    self.terminate_vpn(proc)
                    self._cleanup_temp_files(config_file_path, status_file_path)
                    # clear_iptables_rules() should have been called by setup_iptables_rules on failure
                    return False  # Indicate failure

            print(get_text("setup_finished"))

            # --- Monitor Connection ---
            # Pass the file paths and the process handle
            connection_result = self.vpn_monitor(
                status_file_path, config_file_path, proc, require_delayed_prompt
            )

            # vpn_monitor now returns True if interrupted by user (Ctrl+C), False if connection lost/failed.
            # Cleanup is handled within vpn_monitor or its exception handler.
            # If iptables were set, they are cleared within vpn_monitor on exit/failure.
            return connection_result  # Return status from monitor

        except KeyboardInterrupt:
            self.log.info(
                get_text("received_keyboard_interrupt") + " during connection setup."
            )
            if proc:
                self.terminate_vpn(proc)
            self._cleanup_temp_files(config_file_path, status_file_path)
            if self.args.iptables and is_linux:
                self.clear_iptables_rules()  # Ensure cleanup on interrupt too
            # Re-raise KeyboardInterrupt if needed by calling script, or exit
            # For now, assume we exit gracefully from here
            sys.exit(0)  # Or return False depending on desired caller behavior
        except Exception as e:
            self.log.exception(f"An unexpected error occurred during connect: {e}")
            if proc:
                self.terminate_vpn(proc)
            self._cleanup_temp_files(config_file_path, status_file_path)
            if self.args.iptables and is_linux:
                self.clear_iptables_rules()
            return False  # Indicate failure
        finally:
            # Final cleanup check, although it should be handled above
            # self._cleanup_temp_files(config_file_path, status_file_path) # Maybe redundant
            pass

    def _cleanup_temp_files(self, config_file, status_file):
        """Safely remove temporary config and status files."""
        for f_path in [config_file, status_file]:
            try:
                if f_path and os.path.exists(f_path):
                    os.remove(f_path)
                    self.log.debug(f"Removed temporary file: {f_path}")
            except OSError as e:
                self.log.warning(f"Could not remove temporary file {f_path}: {e}")
            except Exception as e:
                self.log.warning(f"Error removing temporary file {f_path}: {e}")

    def vpn_monitor(
        self, status_file_path, config_file_path, proc, require_delayed_prompt
    ):
        """
        Monitors the VPN connection status using the OpenVPN status file.
        Handles saving qualified VPNs, retries on potential stalls, user prompts,
        and cleanup.

        Args:
            status_file_path (str): Path to the OpenVPN status file.
            config_file_path (str): Path to the temporary OpenVPN config file.
            proc (subprocess.Popen): The OpenVPN process object.
            require_delayed_prompt (bool): Whether to prompt the user after 10s
                                           (used when speedtest fails).

        Returns:
            bool: True if the monitoring loop was exited via KeyboardInterrupt (user stopped),
                  False if the connection was lost or failed the delayed prompt.
        """

        def read_stats(file_path):
            stats = {
                "tun_tap_read": 0,
                "tun_tap_write": 0,
                "tcp_udp_read": 0,
                "tcp_udp_write": 0,
                "auth_read": 0,
                "timestamp": 0,  # Add timestamp for better tracking
            }
            try:
                # Ensure file exists before trying to open
                if not os.path.exists(file_path):
                    self.log.warning(f"Status file not found: {file_path}")
                    return None  # Indicate file not found

                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.readlines()  # Read all lines once

                if not content:
                    self.log.warning(f"Status file is empty: {file_path}")
                    return None  # Indicate empty file

                # Find the header line to get timestamp
                header_line = next(
                    (line for line in content if line.startswith("Updated")), None
                )
                if header_line:
                    try:
                        # Example: Updated,Thu Apr 27 10:30:01 2023
                        # For simplicity, just use current time if parsing fails,
                        # but ideally parse the timestamp from the file
                        stats["timestamp"] = time.time()  # Fallback
                    except Exception:
                        stats["timestamp"] = time.time()  # Fallback on parsing error

                # Find data lines (Version 3 stats start with specific prefixes)
                for line in content:
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        key = parts[0]
                        value_str = parts[1]
                        try:
                            value = int(value_str)
                            if key == "TUN/TAP read bytes":
                                stats["tun_tap_read"] = value
                            elif key == "TUN/TAP write bytes":
                                stats["tun_tap_write"] = value
                            elif key == "TCP/UDP read bytes":
                                stats["tcp_udp_read"] = value
                            elif key == "TCP/UDP write bytes":
                                stats["tcp_udp_write"] = value
                            elif key == "Auth read bytes":
                                stats["auth_read"] = value
                        except ValueError:
                            # Ignore lines where the second part isn't an integer
                            continue
            except IOError as e:
                self.log.error(f"Could not read status file {file_path}: {e}")
                return None  # Indicate read error
            except Exception as e:
                self.log.exception(
                    f"Unexpected error reading stats from {file_path}: {e}"
                )
                return None  # Indicate other error
            return stats

        def format_speed(speed_mbps):
            """Formats speed in MB/s or KB/s."""
            if speed_mbps < 1.0:
                return f"{speed_mbps * 1024:.1f} KB/s"
            else:
                return f"{speed_mbps:.2f} MB/s"

        def format_elapsed_time(elapsed_time_second):
            """Formats elapsed time from seconds to a human-readable string."""
            f_elapsed_time = timedelta(seconds=int(elapsed_time_second))
            return str(f_elapsed_time)  # Convert timedelta to string

        start_time = time.time()
        previous_stats = None
        no_change_counter = 0
        monitor_interval = (
            1  # Sync with status file update interval (set to 1s in build_ovpn_command)
        )
        max_retries = (
            15  # Number of intervals with no change before declaring disconnect
        )

        try:
            # Initial read
            time.sleep(monitor_interval)  # Wait for the first status update
            previous_stats = read_stats(status_file_path)
            if previous_stats is None:
                # Status file couldn't be read initially
                raise IOError(f"Initial read of status file failed: {status_file_path}")

            while True:
                time.sleep(monitor_interval)
                current_stats = read_stats(status_file_path)
                elapsed_time = time.time() - start_time

                # Handle delayed prompt if needed
                if require_delayed_prompt and elapsed_time > 15:
                    print()  # 新行
                    print("\r连接保持 10 秒,也许可用...", end="\r")
                    use_this_vpn = self.prompt_use_vpn()
                    require_delayed_prompt = False  # Prompt only once
                    if not use_this_vpn:
                        print("\033[33m" + get_text("next_vpn") + "\033[0m")
                        # Terminate, cleanup, and return False from monitor
                        self.terminate_vpn(proc)
                        self._cleanup_temp_files(config_file_path, status_file_path)
                        if self.args.iptables and is_linux:
                            self.clear_iptables_rules()
                        return False  # User rejected after delay

                # # Check if stats reading failed
                # if current_stats is None:
                #     self.log.warning(
                #         "Failed to read current stats. Incrementing no_change_counter."
                #     )
                #     no_change_counter += 1

                # Check if stats haven't changed
                elif (
                    previous_stats  # Ensure previous_stats is not None
                    and current_stats["tun_tap_read"] == previous_stats["tun_tap_read"]
                    and current_stats["tun_tap_write"]
                    == previous_stats["tun_tap_write"]
                    and current_stats["tcp_udp_read"] == previous_stats["tcp_udp_read"]
                    and current_stats["tcp_udp_write"]
                    == previous_stats["tcp_udp_write"]
                    and current_stats["auth_read"] == previous_stats["auth_read"]
                ):
                    no_change_counter += 1
                    self.log.debug(
                        f"No change detected in stats. Counter: {no_change_counter}"
                    )
                else:
                    # Stats changed or this is the first valid read after an error
                    no_change_counter = 0  # Reset counter on activity

                    # Calculate speed (bytes per interval -> MB/s)
                    # Use max(1, ...) to avoid division by zero if interval is too short or stats update instantly
                    read_interval = (
                        current_stats["timestamp"] - previous_stats["timestamp"]
                        if previous_stats
                        else monitor_interval
                    )
                    read_interval = max(
                        1e-6, read_interval
                    )  # Avoid division by zero or negative

                    bytes_read = (
                        current_stats["tun_tap_read"] - previous_stats["tun_tap_read"]
                        if previous_stats
                        else current_stats["tun_tap_read"]
                    )
                    bytes_written = (
                        current_stats["tun_tap_write"] - previous_stats["tun_tap_write"]
                        if previous_stats
                        else current_stats["tun_tap_write"]
                    )

                    # Convert bytes per interval to MB/s
                    read_speed_mbps = (bytes_read / read_interval) / (1024 * 1024)
                    write_speed_mbps = (bytes_written / read_interval) / (1024 * 1024)

                    # Print status
                    if write_speed_mbps >= 0 and read_speed_mbps >= 0:
                        print(
                            f"\r -{get_text("connected")}: {format_elapsed_time(elapsed_time):>7s} | "
                            f"{get_text("download")}: {current_stats['tun_tap_write']/(1024*1024):4.0f} MB | "
                            f"{get_text("down")}: {format_speed(write_speed_mbps):>10s} | "
                            f"{get_text("up")}: {format_speed(read_speed_mbps):>10s}",
                            end="",
                            flush=True,
                        )

                    # Check for qualified VPN condition (only once)
                    qualified_time_in_second = self.args.qualified_time * 60
                    if (
                        elapsed_time >= qualified_time_in_second
                        and not self.saved_as_qualified
                    ):
                        print(
                            "\r",
                            get_text("checking_if_qualified")
                            % (self.args.qualified_time),
                            end="\r",
                        )

                        # Check if the specific config file already exists (proxy for already saved)
                        if self.qualified_vpn_config_path and not os.path.exists(
                            self.qualified_vpn_config_path
                        ):
                            self.log.debug(
                                f"\r将要保存优质配置到: {self.qualified_vpn_config_path}"
                            )
                            # os.makedirs(CONFIG_DIR, exist_ok=True)
                            try:
                                # if is_linux:
                                #     # Set permissions more securely if possible, 0o777 is very open
                                #     # Consider 0o775 or 0o755 depending on user/group needs
                                #     os.chmod(
                                #         CONFIG_DIR, 0o777
                                #     )  # Keep original behavior for now

                                # Save .ovpn config
                                with open(
                                    self.qualified_vpn_config_path,
                                    "w",
                                    encoding="utf-8",
                                ) as f:  # Use 'w' to overwrite/create
                                    f.write(self.config)  # Write the original config
                                self.log.debug(
                                    f"\033[32mVPN连接稳定，保存配置到文件\n {self.qualified_vpn_config_path}。\033[0m"
                                )  # Newline before message

                                # Save VPN info to CSV file
                                if self.qualified_vpn_csv_path:
                                    vpn_data = {
                                        "IP": self.ip,
                                        "Port": self.port,
                                        "Country": self.country,
                                        "CountryCode": self.country_code,
                                        "Protocol": self.proto,
                                        # Re-encode the original config string
                                        "ConfigBase64": base64.b64encode(
                                            self.config.encode("utf-8")
                                        ).decode("utf-8"),
                                    }
                                    file_exists = os.path.exists(
                                        self.qualified_vpn_csv_path
                                    )
                                    with open(
                                        self.qualified_vpn_csv_path,
                                        mode="a",
                                        newline="",
                                        encoding="utf-8",
                                    ) as csvfile:
                                        fieldnames = [
                                            "IP",
                                            "Port",
                                            "Country",
                                            "CountryCode",
                                            "Protocol",
                                            "ConfigBase64",
                                        ]
                                        writer = csv.DictWriter(
                                            csvfile, fieldnames=fieldnames
                                        )
                                        if (
                                            not file_exists
                                            or os.path.getsize(
                                                self.qualified_vpn_csv_path
                                            )
                                            == 0
                                        ):
                                            writer.writeheader()  # Write header if new file or empty
                                        writer.writerow(vpn_data)
                                    print(
                                        get_text(
                                            "VPN Connected stable in n minutes, save VPN config in CSV file"
                                        )
                                        % (
                                            self.args.qualified_time,
                                            self.qualified_vpn_csv_path,
                                        )
                                    )
                                    # if is_linux:
                                    #     os.chmod(self.qualified_vpn_csv_path, 0o777)

                                self.saved_as_qualified = (
                                    True  # Mark as saved for this run
                                )

                            except (IOError, OSError, csv.Error) as e:
                                self.log.error(
                                    f"Failed to save qualified VPN info: {e}"
                                )
                                # Optionally remove the .ovpn file if CSV writing failed to keep consistent
                                if os.path.exists(self.qualified_vpn_config_path):
                                    try:
                                        os.remove(self.qualified_vpn_config_path)
                                    except OSError:
                                        pass  # Ignore error during cleanup rollback
                            except Exception as e:
                                self.log.exception(
                                    f"Unexpected error saving qualified VPN: {e}"
                                )

                        elif self.saved_as_qualified:
                            self.log.debug(
                                "Already saved as qualified during this run."
                            )
                        else:
                            print(
                                get_text(
                                    "Qualified config file already exists. Skipping save."
                                )
                                % (self.qualified_vpn_config_path),
                                end="\r",
                            )
                            self.saved_as_qualified = (
                                True  # Also mark as saved if file pre-exists
                            )

                    # Update previous stats for the next iteration
                    previous_stats = current_stats

                # Check for disconnect condition (too many intervals with no change)
                if no_change_counter >= max_retries:
                    print()  # Newline after status print
                    self.log.warning(
                        get_text("connection_disconnected")
                        + get_text("(No status change for %s seconds)"),
                        no_change_counter * monitor_interval,
                    )
                    self.terminate_vpn(proc)
                    self._cleanup_temp_files(config_file_path, status_file_path)
                    if self.args.iptables and is_linux:
                        self.clear_iptables_rules()
                    return False  # Indicate connection failure

                # Check if the OpenVPN process itself has exited unexpectedly
                if proc.poll() is not None:
                    print()  # Newline after status print
                    self.log.error(
                        get_text("connection_disconnected") + f"code: {proc.returncode}"
                    )
                    # No need to call terminate_vpn as it already exited
                    self._cleanup_temp_files(config_file_path, status_file_path)
                    if self.args.iptables and is_linux:
                        self.clear_iptables_rules()
                    return False  # Indicate connection failure

        except KeyboardInterrupt:
            print()  # Newline after status print
            self.log.info(get_text("received_keyboard_interrupt"))
            self.terminate_vpn(proc)
            self._cleanup_temp_files(config_file_path, status_file_path)
            if self.args.iptables and is_linux:
                self.clear_iptables_rules()
            # sys.exit(0) # Original behavior: exit script
            return False  # Modified: Indicate user interruption to caller

        except (IOError, OSError) as e:
            print()  # Newline after status print
            self.log.error(f"I/O Error during monitoring: {e}")
            self.terminate_vpn(proc)
            self._cleanup_temp_files(config_file_path, status_file_path)
            if self.args.iptables and is_linux:
                self.clear_iptables_rules()
            return False  # Indicate failure

        except Exception as e:
            print()  # Newline after status print
            self.log.exception(f"An unexpected error occurred during vpn_monitor: {e}")
            self.terminate_vpn(proc)
            self._cleanup_temp_files(config_file_path, status_file_path)
            if self.args.iptables and is_linux:
                self.clear_iptables_rules()
            return False  # Indicate failure

        # This part should ideally not be reached in the loop structure
        finally:
            print()  # Ensure newline after last status update or error message
            self.log.info(
                get_text("connection_closed") % (self.ip, self.port, self.country_code)
            )

    def build_ovpn_command(self, conffile):
        # Ensure TEMP_DIR exists
        os.makedirs(TEMP_DIR, exist_ok=True)
        statusFile = os.path.join(
            TEMP_DIR, f"vpn_status_{self.ip}_{self.port}.log"
        )  # More specific name

        # Base command
        command = [
            "openvpn",
            "--verb",
            "4",  # Verb 3 is usually sufficient, 4 is debug level
            "--script-security",
            "2",
            # Retry/timeout settings (consider adjusting based on typical connection times)
            "--connect-retry-max",
            "4",  # Max connection attempts before failing
            # "--connect-timeout", "10", # Timeout for initial TCP/UDP connection (seconds) - was 3
            # "--server-poll-timeout", "10", # How long to wait for server response after connection
            "--connect-timeout",
            str(self.args.vpn_timeout),  # Use arg if available
            # Ping settings for keepalive and detecting dead connections
            "--keepalive",
            "1",
            "15",  # Ping every 10s, assume dead after 60s silence
            # Use ping-exit/restart instead of keepalive if preferred (original code used them)
            # "--ping-exit", "60", # Exit after 60 seconds of ping timeout (was 3) - Increased
            # "--ping-restart", # Restart if ping fails for 180s (higher than exit) - Adjust if needed (was 3)
            # "5",
            # Status file settings
            "--status",
            statusFile,
            "1",  # Write status every 1 second
            "--status-version",
            "3",  # Use version 3 format (easier to parse)
        ]

        # Add config file
        command.extend(["--config", conffile])

        # Add platform-specific options if needed
        # e.g., --dev tun0 on Linux, --dev tap on Windows (often auto-detected)

        # Authentication (if needed, e.g., --auth-user-pass pass.txt)
        # Add logic here if username/password auth is required

        # self.log.debug(f"Built OpenVPN command: {' '.join(command)}")
        self.log.debug(f"Status file will be: {statusFile}")
        return command, statusFile

    def wait_for_vpn_ready(self, proc, conffileName):
        """Waits for the VPN process to signal readiness or timeout/fail."""
        self.log.info(get_text("Waiting for VPN initialization..."))
        # Use a clearer timeout mechanism based on start time
        start_wait_time = time.time()
        timeout_seconds = self.args.vpn_timeout  # Use timeout from args

        try:
            while time.time() - start_wait_time < timeout_seconds:
                # Check if process terminated prematurely
                return_code = proc.poll()
                if return_code is not None:
                    self.log.error(
                        f"{get_text('vpn_init_failed')} - Process exited with code {return_code}"
                    )
                    # Read stderr for more details
                    stderr_output = proc.stderr.read()
                    if stderr_output:
                        self.log.error(f"OpenVPN stderr:\n{stderr_output.strip()}")
                    else:
                        # If stderr is empty, check stdout
                        stdout_output = proc.stdout.read()
                        if stdout_output:
                            self.log.error(f"OpenVPN stdout:\n{stdout_output.strip()}")
                    return False

                # Check stdout for success message non-blockingly
                # Note: proc.stdout.readline() blocks if used directly here.
                # Reading all available lines is safer in a loop.
                # However, the Popen setup uses PIPE, so readline should work.
                # Add a small sleep to prevent busy-waiting.
                try:
                    # This might still block if no newline is sent for a long time.
                    # Using select or threads is more robust but complex.
                    # Assuming OpenVPN sends lines reasonably often.
                    line = proc.stdout.readline()
                    if not line:
                        # End of stream (shouldn't happen if process is running unless stdout closed)
                        time.sleep(
                            self.args.vpn_timeout_poll_interval
                        )  # Wait before checking again
                        continue

                    line_strip = line.strip()
                    if self.args.verbose:
                        # Use non-ANSI codes for simple logging if needed, or keep ANSI
                        print("\033[90m" + line_strip + "\033[0m")

                    if "Initialization Sequence Completed" in line_strip:
                        Init_time = time.time() - start_wait_time
                        Init_time = f"{Init_time:.1f}"
                        print(  # Clear screen and print success
                            "\033[2J\033[H\033[0m"
                            + (
                                get_text("vpn_init_success")
                                % (
                                    self.country_code,
                                    self.ip,
                                    self.port,
                                    self.proto,
                                    Init_time,
                                )
                            )
                        )
                        # Do not close stdout here, monitor might need it (though unlikely)
                        # proc.stdout.close() # Reconsider closing stdout
                        for remaining in range(10, 0, -1):
                            print(
                                f"\033[90m等待网络设置完成 ({remaining}s)...\033[0m",
                                end="\r",
                            )
                            time.sleep(1)  # 每秒更新倒计时
                        print("\033[90m网络设置完成，开始下载测试。\033[0m", end="\r")
                        return True

                except IOError:
                    # Handle cases where the pipe might be broken
                    self.log.warning(
                        "IOError reading OpenVPN stdout, process might have issues."
                    )
                    time.sleep(self.args.vpn_timeout_poll_interval)
                    continue

                # Wait a short interval before checking again
                time.sleep(self.args.vpn_timeout_poll_interval)  # e.g., 0.1 seconds

            # Loop finished without success message = Timeout

            self.log.info("\033[33m" + get_text("vpn_init_timeout") + "\033[0m")
            # Don't close stdout here either, let terminate_vpn handle process
            # proc.stdout.close()
            # self.terminate_vpn(proc) # Terminate is handled in the caller (`connect`)
            return False

        except KeyboardInterrupt:
            self.log.info(get_text("received_keyboard_interrupt") + " during VPN wait.")
            # Cleanup handled by the caller's exception block
            raise  # Re-raise for the caller to handle termination/cleanup

        except Exception as e:
            self.log.exception(f"Unexpected error waiting for VPN ready: {e}")
            return False  # Indicate failure

    def prompt_use_vpn(self):
        """Asks the user if she likes to continue using the VPN connection.
          Automatically returns True after a 5-second timeout.

        Returns:
            (boolean) True if the users wants to use this VPN (or timeout),
                      False if not (e.g., presses Ctrl+C or types 'n').
        """
        timeout = 5
        try:
            if sys.platform == "win32":
                import msvcrt

                input_str = ""
                for remaining in range(timeout, 0, -1):
                    print(
                        f"\r{get_text('use_or_change')} \033[90m({remaining} 秒)\033[0m",
                        end="",
                        flush=True,
                    )
                    start_time = time.time()
                    while time.time() - start_time < 1:
                        if msvcrt.kbhit():
                            ch = msvcrt.getwch()
                            if ch in ("\r", "\n"):
                                print()
                                response = input_str.strip().lower()
                                if response in ["n", "no", "q", "quit"]:
                                    return False
                                return True
                            elif ch in ("\x03", "\x1a"):
                                print()
                                raise KeyboardInterrupt
                            elif ch == "\b":
                                input_str = input_str[:-1]
                            else:
                                input_str += ch
                        time.sleep(0.05)
                print("\r自动确认，进入连接监测模式. ", end="\r", flush=True)
                return True
            else:
                if sys.stdin.isatty():
                    import select

                    print(
                        f"\r{get_text('use_or_change')} \033[90m({timeout} 秒)\033[0m",
                        end="",
                        flush=True,
                    )
                    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                    if rlist:
                        response = sys.stdin.readline().strip().lower()
                        if response in ["n", "no", "q", "quit"]:
                            return False
                        return True
                    else:
                        print("\r自动确认，进入连接监测模式. ", end="\r", flush=True)
                        return True
                else:
                        print("\r自动确认，进入连接监测模式. ", end="\r", flush=True)
                        return True

        except KeyboardInterrupt:
            print()  # Newline after prompt
            self.log.info("User interrupted prompt.")
            return False  # Treat interrupt as "no"

    def terminate_vpn(self, proc):
        """Terminates the given vpn process gracefully (or forcefully if needed).

        Arguments:
            (Popen) proc: The Popen object for the openvpn process.
        """
        if proc is None or proc.poll() is not None:
            self.log.debug("VPN process already terminated or not started.")
            return  # Nothing to terminate

        pid = proc.pid
        self.log.info(f"{get_text('terminating_vpn')} \033[90m(PID: {pid})\033[0m")

        # --- Graceful Termination (SIGTERM) ---
        try:
            # proc.terminate() sends SIGTERM on Unix, TerminateProcess on Windows
            proc.terminate()
            self.log.debug(f"Sent SIGTERM to PID {pid}.")
        except ProcessLookupError:
            self.log.warning(
                f"Process with PID {pid} not found for termination (already gone?)."
            )
            return  # Process doesn't exist anymore
        except Exception as e:
            # Catch other potential errors during terminate()
            self.log.error(f"Error trying to send SIGTERM to PID {pid}: {e}")
            # Proceed to check/force kill anyway

        # --- Wait for Termination ---
        try:
            # Wait for up to 5 seconds for the process to exit
            proc.wait(timeout=5)
            self.log.info(f"{get_text('vpn_terminated')}")
            return  # Success
        except subprocess.TimeoutExpired:
            self.log.warning(
                f"{get_text('termination_timeout')} (PID: {pid}). Attempting forceful kill (SIGKILL)."
            )
        except Exception as e:
            # Catch errors during wait() (though less common)
            self.log.error(f"Error waiting for process {pid} to terminate: {e}")
            # Proceed to force kill

        # --- Forceful Termination (SIGKILL) ---
        # If graceful termination failed or timed out
        try:
            # proc.kill() sends SIGKILL on Unix, TerminateProcess on Windows (same as terminate)
            # On Unix, sending SIGKILL explicitly might be more robust if SIGTERM was ignored
            if hasattr(os, "kill"):  # Check if os.kill is available (Unix-like)
                os.kill(pid, signal.SIGKILL)
                self.log.debug(f"Sent SIGKILL to PID {pid}.")
            else:
                proc.kill()  # Fallback for Windows or if os.kill isn't used
                self.log.debug(f"Called proc.kill() for PID {pid}.")

            # --- Final Wait after SIGKILL ---
            try:
                proc.wait(timeout=2)  # Wait briefly after SIGKILL
                self.log.info(
                    f"VPN process force-killed (PID: {pid}). Exit code: {proc.returncode}"
                )
            except subprocess.TimeoutExpired:
                self.log.critical(
                    f"{get_text('vpn_unkillable')} (PID: {pid}) after SIGKILL."
                )
                self.log.critical(get_text("exiting"))
                # Decide on action: exit script or just log error?
                sys.exit(1)  # Exit script if VPN can't be killed
            except Exception as e:
                self.log.error(f"Error waiting after SIGKILL for process {pid}: {e}")

        except ProcessLookupError:
            self.log.warning(
                f"Process with PID {pid} not found for SIGKILL (already gone?)."
            )
        except Exception as e:
            self.log.error(f"Error trying to send SIGKILL to PID {pid}: {e}")
            # If even kill fails, log critical error
            self.log.critical(
                f"Failed to force kill process {pid}. Manual intervention may be required."
            )

    def vpncheck(self):
        """
        Performs a speed test on the VPN connection.

        Returns:
            bool or str:
                True if download speed >= min_speed.
                False if download speed < min_speed.
                'error' if speedtest returns 9999 (indicating an error).
        """

        print("\r" + get_text("performing_speedtest"), end="\r")

        try:
            # Assuming speedtest() returns speed in Mbps or a specific error code
            # Need to know the exact return units/values of the actual speedtest function
            download_speed_MBps = speedtest()  # Placeholder call

            if download_speed_MBps is None:
                # Requirement 2: Handle specific error code
                print("\033[30m" + get_text("error_download_speed") + "\033[0m")
                return "error"  # Special return value for this case
            if download_speed_MBps == "error":
                # Requirement 2: Handle specific error code
                print("\033[31m" + get_text("failed_download_speed") + "\033[0m")
                return False
            elif download_speed_MBps < self.args.min_speed:
                print(
                    "\033[31m"
                    + get_text("bad_download_speed")
                    + f" ({download_speed_MBps:.2f} Mbps)"
                    + "\033[0m"
                )
                return False
            else:
                # Speed is acceptable
                return True
        except KeyboardInterrupt:
            print("\n" + get_text("speedtest_canceled"))  # Newline for clarity
            # Treat cancellation as user wanting to proceed but skip test result check
            # Or treat as wanting to abort this VPN? Let's assume proceed cautiously.
            return "error"  # Treat cancellation similar to error - proceed to monitor/prompt
        except Exception as e:
            # Handle potential errors within the speedtest function itself
            self.log.exception(f"Error during speedtest execution: {e}")
            print("\033[31m" + "速度测试期间发生错误。" + "\033[0m")
            return "error"  # Treat generic errors same as specific error code

    def setup_iptables_rules(self):
        return self.firewall.setup_rules()

    def clear_iptables_rules(self):
        self.firewall.clear_rules()

    def __str__(self):
        # Ensure attributes exist before formatting
        ip_str = getattr(self, "ip", "N/A")
        cc_str = getattr(self, "country_code", "N/A")
        proto_str = getattr(self, "proto", "N/A")
        port_str = getattr(self, "port", "N/A")
        return f"ip={ip_str:<15}, country={cc_str}, proto={proto_str}, port={port_str}"


class FileVPN(VPNClient):
    """A VPN whose config is read directly from an .openvpn file"""

    def __init__(self, args):
        conf = args.ovpnfile.read()
        b64conf = base64.b64encode(conf)

        data = {
            "IP": None,
            "CountryLong": "Unknown",
            "CountryShort": "Unknown",
            "#HostName": args.ovpnfile.name,
            "OpenVPN_ConfigData_Base64": b64conf,
        }

        super().__init__(data, args)


def check_call_infallible(cmd):
    """Calls subprocess.check_call() and returns False if the process exits
    with non-zero exit code instead of throwing CalledProcessException

    Arguments:
        (Array) cmd - The command to execute.

    Returns:
        (boolean) True if command succeeded, False otherwise.
    """
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        return False
    return True


class VPNList:
    def __init__(self, args):
        print("\033[2J\033[H\033[32m" + get_text("vpn_start_running") + "\033[0m")
        self.args = args
        # Logging
        self.log = logging.getLogger(self.__class__.__name__)  # 自动获取类名

        # Initialize separate lists
        self.qualified_vpns = []
        self.main_vpns = []

        # --- Loading ---
        # Check if the main list CSV file exists and is not expired
        self.local_csv_path = os.path.join(CACHE_DIR, LOCAL_CSV_NAME)
        if self.is_file_expired(self.local_csv_path):
            self.log.info(get_text("vpnlist_expired"))
            # Make sure download_vpn_list is defined or imported
            self.download_vpn_list(self.args.url, self.local_csv_path)

        # Load both lists
        self.load_vpns(self.local_csv_path)  # Pass main list path

        # --- Filtering ---
        # Filter both lists by country
        self.filter_by_country()

        # Filter out unresponsive servers from both lists
        self.filter_unresponsive_vpns()

        # Log final counts
        self.log.info(
            get_text("Loaded_and_filtered_vpn_lists"),
            len(self.qualified_vpns) + len(self.main_vpns),
            len(self.qualified_vpns),
            len(self.main_vpns),
        )

    def is_file_expired(self, file_path):
        """Check if the file is older than the specified number of hours."""
        if not os.path.exists(file_path):
            return True
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        return datetime.now() - file_mod_time > timedelta(hours=self.args.expired_time)

    def check_proxy(self, proxy_url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            req = urllib.request.Request(proxy_url, headers=headers)
            # 创建上下文以处理SSL验证
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            response = urllib.request.urlopen(req, timeout=5, context=context)
            # 如果状态码是200，表示代理URL可用
            return response.status == 200
        except (urllib.error.URLError, urllib.error.HTTPError):
            # self.log.error(f"Proxy check failed for {proxy_url}: {e}")
            self.log.error(get_text("proxy_check_failed"), proxy_url)
            return False

    # Returns the first available GitHub Proxy
    def get_available_GitHub_proxy(self):
        proxies = [
            "https://ghproxy.net/",
            "https://gh.llkk.cc/",
            "https://ghp.ci/",
            "https://ghproxy.cn/",
            "https://github.akams.cn/",
        ]

        for proxy in proxies:
            if self.check_proxy(proxy):
                self.log.info(get_text("available_GitHub_proxy"), proxy)
                return proxy

        return None

    # 常见代理端口，用于尝试通过不同端口下载列表
    COMMON_PROXY_PORTS = {
        "10808",
        "7890",
        "10809",
    }

    def _detect_proxy_port(self):
        """检测可用的代理端口"""

        def check_port(port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.1)
                    if sock.connect_ex(("127.0.0.1", int(port))) == 0:
                        return True, port
            except Exception:
                pass
            return False, None

        for port in self.COMMON_PROXY_PORTS:
            success, port = check_port(port)
            if success:
                self.log.info(get_text("proxy_running"), port)
                return True, port

        return False, None

    def download_vpn_list(self, url, file_path, backup_proxy=None):
        """Download the VPN list from the given URL and save it to the specified file path."""
        self.log.info(get_text("download_from_main_url"), url)

        proxy_running, port = self._detect_proxy_port()

        try:
            if proxy_running:
                try:
                    # Download with proxy
                    proxy = urllib.request.ProxyHandler(
                        {
                            "http": f"http://localhost:{port}",
                            "https": f"https://localhost:{port}",
                        }
                    )
                    opener = urllib.request.build_opener(proxy)
                    urllib.request.install_opener(opener)

                    req = urllib.request.urlopen(url, timeout=10)
                    data = req.read()

                    # Check if the data is valid
                    if (
                        not data or len(data) < 1000
                    ):  # Assuming valid data should be larger than 100 bytes
                        raise ValueError(get_text("invalid_vpnlist_data"))

                    with open(file_path, "wb") as f:
                        f.write(data)
                    self.log.info(get_text("vpnlist_download_saved_to_file"), file_path)
                except Exception as e:
                    self.log.debug(f"system proxy error: {e}")
                    raise Exception
            else:
                raise Exception
        except Exception:
            self.log.error(get_text("failed_to_download_from_main_url"))
            original_url = "https://raw.githubusercontent.com/sinspired/VpngateAPI/main/servers.csv"

            # Check available proxies and set an alternate download address
            available_proxy = self.get_available_GitHub_proxy()
            if available_proxy:
                backup_url = f"{available_proxy}{original_url}"
                self.log.info(
                    get_text("attempt_download_from_backup_url"),
                    backup_url,
                )
            else:
                if backup_proxy:
                    backup_url = f"{backup_proxy}{original_url}"
                    self.log.info(
                        get_text("attempt_download_from_backup_url"),
                        backup_url,
                    )
                else:
                    backup_url = original_url
                    self.log.info(
                        get_text("attempt_download_from_backup_url"),
                        backup_url,
                    )

            try:
                # Uninstall proxy
                urllib.request.install_opener(None)
                req = urllib.request.urlopen(backup_url)
                data = req.read()
                with open(file_path, "wb") as f:
                    f.write(data)
                self.log.info(get_text("vpnlist_download_saved_to_file"), file_path)
            except Exception:
                self.log.error(
                    get_text("failed_to_download_from_backup_url"), backup_url
                )

    def load_vpns(self, main_list_file_path):
        """Loads qualified VPNs and main list VPNs into separate lists."""
        self.log.info(get_text("loading_vpn_list"))

        # 1. Load Qualified VPNs from configs folder
        qualified_loaded_count = 0
        if os.path.exists(CONFIG_DIR):  # Assume CONFIGS_DIR is defined
            qualified_vpn_csv = os.path.join(CONFIG_DIR, "qualified_vpns.csv")
            if os.path.exists(qualified_vpn_csv):
                try:
                    with open(qualified_vpn_csv, "r", encoding="utf-8") as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            try:
                                config_data = base64.b64decode(
                                    row["ConfigBase64"]
                                ).decode("utf-8")
                                vpn_data = {
                                    "IP": row["IP"],
                                    "CountryLong": row["Country"],
                                    "CountryShort": row["CountryCode"],
                                    "#HostName": f"{row['IP']}:{row['Port']}",  # Construct HostName if needed by VPN class
                                    "OpenVPN_ConfigData_Base64": base64.b64encode(
                                        config_data.encode("utf-8")
                                    ).decode("utf-8"),
                                    # Add other fields expected by your VPN class constructor if necessary
                                }
                                # Assuming VPN class takes (vpn_data_dict, args)
                                self.qualified_vpns.append(
                                    VPNClient(vpn_data, self.args)
                                )
                                qualified_loaded_count += 1
                            except Exception as e:
                                self.log.error(
                                    f"Error parsing row from qualified_vpns.csv: {row} - {e}"
                                )
                    if qualified_loaded_count > 0:
                        self.log.info(
                            get_text("found_vpn_servers"),
                            qualified_vpn_csv,
                            qualified_loaded_count,
                        )
                    else:
                        self.log.info(
                            f"Found {qualified_vpn_csv}, but no VPNs were loaded from it."
                        )
                except Exception as e:
                    self.log.error(
                        f"Failed to read or process {qualified_vpn_csv}: {e}"
                    )
            else:
                self.log.debug(get_text("file_path_not_found"), qualified_vpn_csv)
        else:
            self.log.info(f"Configs directory not found: {CONFIG_DIR}")

        # 2. Load Main VPN list
        main_list_loaded_count = 0
        if not os.path.exists(main_list_file_path):
            self.log.error(get_text("file_path_not_found"), main_list_file_path)
            # Decide if you want to exit(1) here or just continue with an empty main list
            # sys.exit(1) # Optional: exit if main list is absolutely required
        else:
            try:
                with open(main_list_file_path, "r", encoding="utf8") as f:
                    # Skip comment lines starting with '*' or '#' (adjust if needed)
                    rows = filter(lambda r: not r.startswith("*"), f)
                    reader = csv.DictReader(rows)
                    # Assuming VPN class takes (row_dict, args)
                    self.main_vpns = [VPNClient(row, self.args) for row in reader]
                    main_list_loaded_count = len(self.main_vpns)
                self.log.info(
                    get_text("found_vpn_servers"),
                    main_list_file_path,
                    main_list_loaded_count,
                )
            except Exception as e:
                self.log.error(
                    f"Failed to read or process main VPN list {main_list_file_path}: {e}"
                )

    def filter_by_country(self):
        """Filters both qualified and main VPN lists based on geographic information."""
        filters = []
        # ... (keep the logic for building the filters list based on args.eu, args.us, args.country)
        if self.args.eu:
            self.log.info("Including VPNs in Europe")
            filters.append(
                lambda vpn: vpn.country_code in EU_COUNTRIES
            )  # Assume EU_COUNTRIES is defined

        if self.args.us:
            self.log.info("Including VPNs in USA")
            filters.append(lambda vpn: vpn.country_code == "US")

        if self.args.country:
            countries = set(map(str.upper, self.args.country))
            self.log.info("Including VPNs in %s", countries)
            filters.append(lambda vpn: vpn.country_code in countries)

        if filters:
            self.log.info("Applying geographic filters...")

            def filter_fn(vpn):
                return any(f(vpn) for f in filters)

            orig_qualified_count = len(self.qualified_vpns)
            orig_main_count = len(self.main_vpns)

            self.qualified_vpns = list(filter(filter_fn, self.qualified_vpns))
            self.main_vpns = list(filter(filter_fn, self.main_vpns))

            self.log.info(
                f"Qualified VPNs after geo filter: {len(self.qualified_vpns)} (from {orig_qualified_count})"
            )
            self.log.info(
                f"Main list VPNs after geo filter: {len(self.main_vpns)} (from {orig_main_count})"
            )
        else:
            # Add a default filter to exclude "CN" if no other filters are applied
            CN_servers = []
            CN_servers.append(lambda vpn: vpn.country_code != "CN")

            self.log.info(get_text("default_filter"), len(CN_servers))
            filters.append(lambda vpn: vpn.country_code != "CN")

    def filter_unresponsive_vpns(self):
        """Probes VPN servers, measures latency, and removes unresponsive ones."""
        self.log.info(get_text("filtering_servers"))

        vpns_to_probe = self.qualified_vpns + self.main_vpns

        if not vpns_to_probe:
            self.log.info("No VPNs to probe.")
            return

        n = self.args.probes  # Number of concurrent probes
        responding_vpns = []

        self.log.info(get_text("probing_vpns_concurrently"), len(vpns_to_probe), n)
        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:
            futures = {ex.submit(vpn.is_listening): vpn for vpn in vpns_to_probe}

            for future in concurrent.futures.as_completed(futures):
                vpn = futures[future]
                try:
                    is_responding, latency = future.result()
                    if is_responding:
                        # 对于UDP协议，latency为udp_latency参数
                        responding_vpns.append((vpn, latency))
                except Exception as e:
                    self.log.exception(f"Availability probe failed for a VPN: {e}")

        # 默认进行排序，除非显式指定 --no-sort-latency
        if not getattr(self.args, "no_sort_latency", False):
            self.log.info(get_text("h_arg_sort_latency"))
            responding_vpns.sort(key=lambda x: x[1])  # Sort by latency (ascending)
        else:
            self.log.info(get_text("h_arg_no_sort_latency"))

        # Update the lists with sorted VPNs
        self.qualified_vpns = [
            vpn for vpn, _ in responding_vpns if vpn in self.qualified_vpns
        ]
        self.main_vpns = [vpn for vpn, _ in responding_vpns if vpn in self.main_vpns]

        self.log.debug(
            "Qualified VPNs after responsiveness filter: %s",
            len(self.qualified_vpns),
        )
        self.log.debug(
            "Main list VPNs after responsiveness filter: %s",
            len(self.main_vpns),
        )


def speedtest():
    """执行网速测试，以KB/s为单位打印连接速度。"""
    url = globals().get(
        "SPEED_TEST_URL", "http://ipv4.download.thinkbroadband.com/20MB.zip"
    )
    match = re.search(r"(\d+)(MB)", url, re.IGNORECASE)

    # 预期文件大小（MB）
    filesize_expected_mb = float(match.group(1)) if match else 20.0
    filesize_expected_bytes = filesize_expected_mb * (1024 * 1024)

    chunk_size = 8192  # 更大的块大小提高效率
    duration = 10  # 最大测试持续时间
    timeout = 15  # 请求超时时间

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # 使用标准库urllib减少依赖
        req = urllib.request.Request(url, headers=headers)
        start_time = time.perf_counter()  # 更精确的时间测量

        with urllib.request.urlopen(req, timeout=timeout) as response:
            file_size = 0
            end_time = start_time + duration

            while True:
                current_time = time.perf_counter()
                if current_time >= end_time:
                    break  # 达到最大测试时间

                chunk = response.read(chunk_size)
                if not chunk:
                    break  # 文件读取完毕

                file_size += len(chunk)
                if file_size >= filesize_expected_bytes:
                    break  # 已下载预期大小的文件

            elapsed_time = time.perf_counter() - start_time

            # 避免除零错误
            if elapsed_time < 0.001:
                elapsed_time = 0.001

            file_size_MB = file_size / (1024 * 1024)
            download_speed_MBps = file_size_MB / elapsed_time
            download_speed_KBps = download_speed_MBps * 1024

            if download_speed_MBps < 1:
                print(
                    f"\r[ Filesize: \033[90;4m{file_size_MB:.2f}\033[0m MB, in \033[90;4m{elapsed_time:.2f}\033[0m s, Download Speed: \033[32;4m{download_speed_KBps:.0f}\033[0m KB/s ]"
                )
            else:
                print(
                    f"\r[ Filesize: \033[90;4m{file_size_MB:.2f}\033[0m MB, in \033[90;4m{elapsed_time:.2f}\033[0m s Download Speed: \033[32;4m{download_speed_MBps:.2f}\033[0m MB/s, \033[90;4m{download_speed_KBps:.0f}\033[0m KB/s ]"
                )

            return download_speed_MBps

    except urllib.error.HTTPError as e:
        print(f"下载失败，HTTP错误: {e.code} - {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"下载失败，URL错误: {e.reason}")
        return None
    except socket.timeout:
        print("下载失败，连接超时")
        return None
    except Exception as e:
        print(f"下载错误: {e}")
        return None


def single_vpn_main(args):
    """Connects to the VPN is the given .ovpn file."""
    vpn = FileVPN(args)
    try:
        vpn.connect()
    except KeyboardInterrupt:
        logging.error("Aborted")


def _try_connect_from_list(
    vpn_list, list_name, start_index, total_overall_count, logger
):
    """Helper function to attempt connecting to VPNs in a list."""
    connection_established = False
    if not vpn_list:
        logger.info(f"No VPNs to try in {list_name} list.")
        return False

    total_in_list = len(vpn_list)
    logger.debug(
        f"Attempting connections from {list_name} list ({total_in_list} VPNs)..."
    )

    for i, vpn in enumerate(vpn_list):
        current_overall_index = start_index + i + 1  # 1-based index
        print(
            "\033[90m------------------------------------------------------------------+\33[0m"
        )
        # Display index within the current list and overall index
        if total_in_list != total_overall_count:
            print(
                f"\033[90m[{list_name} {i + 1}/{total_in_list} ({current_overall_index}/{total_overall_count})]\033[0m {vpn}"
            )
        else:
            print(f"\033[90m[{list_name} {i + 1}/{total_in_list}]\033[0m {vpn}")

        try:
            # Assuming vpn.connect() returns True if user keeps connection, False otherwise
            res = vpn.connect()
            if res:
                logger.info(f"Connection established and confirmed with: {vpn}")
                connection_established = True
                break  # User was happy with this VPN, break the inner loop
            else:
                logger.debug(f"Connection attempt declined or failed for: {vpn}")
                # Continue to the next VPN in the list
        except KeyboardInterrupt:
            logger.warning("\nConnection process interrupted by user.")
            connection_established = (
                True  # Treat interrupt as a stop signal for further attempts
            )
            break
        except Exception as e:
            logger.error(f"Error connecting to VPN {vpn}: {e}", exc_info=True)
            # Continue to the next VPN

    return connection_established


def vpn_list_main(args):
    """Fetches lists of VPNs and connects, prioritizing the qualified list."""
    logger = logging.getLogger("VPNListMain")  # Use a specific logger or the main one
    vpnlist = VPNList(args)  # This now loads and filters both lists

    connection_established = False
    total_qualified = len(vpnlist.qualified_vpns)
    total_main = len(vpnlist.main_vpns)
    total_overall = total_qualified + total_main

    if total_overall == 0:
        logger.warning("No VPNs available after loading and filtering. Exiting.")
        sys.exit(1)  # Exit if absolutely no VPNs are left

    # 1. Try Qualified VPNs
    if total_qualified > 0:
        connection_established = _try_connect_from_list(
            vpnlist.qualified_vpns,
            get_text("qualified"),
            start_index=0,  # Starts from index 0
            total_overall_count=total_overall,
            logger=logger,
        )
    else:
        logger.debug("Skipping qualified VPN list as it is empty.")

    # 2. Try Main List VPNs ONLY if no connection was established from the qualified list
    if not connection_established:
        if total_main > 0:
            connection_established = _try_connect_from_list(
                vpnlist.main_vpns,
                get_text("main_list"),
                start_index=total_qualified,  # Index continues from qualified list size
                total_overall_count=total_overall,
                logger=logger,
            )
        else:
            logger.info("Skipping main VPN list as it is empty.")
    else:
        logger.info(
            "Connection already established from the qualified list. Skipping main list."
        )

    # Cleanup
    try:
        # Make sure TEMP_DIR is defined
        if "TEMP_DIR" in globals() and os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
            logger.info(get_text("delete_tmp_dir"))
        else:
            logger.debug("TEMP_DIR not found or not defined, skipping cleanup.")
    except Exception as e:
        logger.error(get_text("delete_tmp_dir_failed").format(e=e), exc_info=True)

    if not connection_established:
        logger.warning("Failed to establish a connection with any VPN from any list.")

    logger.info(get_text("exiting"))


def isAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def addOpenVPNtoSysPath():
    """Add OpenVPN binary path to system PATH environment variable."""
    if sys.platform == "win32":
        openvpn_paths = [
            r"C:\Program Files\OpenVPN\bin",
            r"C:\Program Files (x86)\OpenVPN\bin",
        ]
    else:
        openvpn_paths = [
            "/usr/sbin",
            "/usr/local/sbin",
            "/usr/bin",
            "/usr/local/bin",
        ]

    current_path = os.environ.get("PATH", "")
    path_separator = ";" if sys.platform == "win32" else ":"
    current_paths = current_path.split(path_separator)

    for openvpn_path in openvpn_paths:
        if os.path.exists(openvpn_path) and openvpn_path not in current_paths:
            os.environ["PATH"] = f"{openvpn_path}{path_separator}{current_path}"
            print(get_text("add_openvpn_path") % openvpn_path)

            if sys.platform == "win32":
                try:
                    import winreg
                    with winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
                    ) as key:
                        winreg.SetValueEx(
                            key, "PATH", 0, winreg.REG_EXPAND_SZ, os.environ["PATH"]
                        )
                    print(get_text("env_path_updated"))
                except Exception as e:
                    print(get_text("failed_update_registry") % e)
            return True

    print(get_text("openvpn_not_found_standard"))
    return False


def parse_args():
    """Parses the command line arguments."""

    p = argparse.ArgumentParser(description=get_text("appDescription"))
    p.add_argument(
        "--country",
        "-c",
        action="append",
        help=get_text("h_arg_country"),
    )
    p.add_argument(
        "--eu",
        action="store_true",
        help=get_text("h_arg_eu"),
    )
    p.add_argument(
        "--iptables",
        "-i",
        action="store_true",
        help=get_text("h_arg_iptables"),
    )
    p.add_argument(
        "--probes",
        action="store",
        default=100,
        type=int,
        help=get_text("h_arg_probes"),
    )
    p.add_argument(
        "--probe-timeout",
        action="store",
        default=10,
        type=int,
        help=get_text("h_arg_probe_timeout"),
    )
    p.add_argument(
        "--url",
        action="store",
        default=VPN_LIST_URL,
        help=get_text("h_arg_url"),
    )
    p.add_argument(
        "--us",
        action="store_true",
        help=get_text("h_arg_us"),
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help=get_text("h_arg_verbose"),
    )
    p.add_argument(
        "--vpn-timeout",
        "-vt",
        action="store",
        default=DEFAULT_VPN_TIMEOUT,
        type=int,
        help=get_text("h_arg_vpn_timeout"),
    )
    p.add_argument(
        "--vpn-timeout-poll-interval",
        action="store",
        default=0.1,
        type=int,
        help=get_text("h_arg_vpn_timeout_poll_interval"),
    )
    p.add_argument(
        "ovpnfile",
        type=argparse.FileType("rb"),
        default=None,
        nargs="?",
        help=get_text("h_arg_ovpnfile"),
    )
    p.add_argument(
        "--expired-time",
        "-et",
        action="store",
        default=DEFAULT_EXPIRED_TIME,
        type=int,
        help=get_text("h_arg_expired_time"),
    )
    p.add_argument(
        "--min-speed",
        "-ms",
        action="store",
        default=DEFAULT_MIN_SPEED,
        type=float,
        help=get_text("h_arg_min_speed"),
    )
    p.add_argument(
        "--qualified-time",
        "-qt",
        action="store",
        default=DEFAULT_QUALIFIED_TIME,
        type=int,
        help=get_text("h_arg_qualified_time"),
    )
    p.add_argument(
        "--no-sort-latency",
        "-ns",
        action="store_true",
        help=get_text("h_arg_no_sort_latency"),
    )
    p.add_argument(
        "--udp-latency",
        "-ul",
        action="store",
        default=SET_UDP_LATENCY,
        type=int,
        help=get_text("h_arg_udp_latency"),
    )
    # 覆盖默认的 help 信息
    p._positionals.title = get_text("positional_arguments")
    p._optionals.title = get_text("optional_arguments")
    p._defaults["help"] = get_text("h_help")

    return p.parse_args()


def customLogger():
    args = parse_args()

    # 自定义时间格式
    def custom_time(*args):
        return datetime.now().strftime("%I:%M%p")

    # 定义颜色常量
    class LogColors:
        BLUE = "\033[34m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RED = "\033[31m"
        RESET = "\033[0m"

    # 自定义格式化器
    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            levelname = record.levelname
            color_map = {
                "DEBUG": LogColors.BLUE,
                "INFO": LogColors.GREEN,
                "WARNING": LogColors.YELLOW,
                "ERROR": LogColors.RED,
                "CRITICAL": LogColors.RED,
            }
            record.levelname = (
                f"{color_map.get(levelname, '')}{levelname}{LogColors.RESET}"
            )
            return super().format(record)

    # 日志格式
    verbose_format = "%(asctime)s %(levelname)s \033[36m%(name)s\033[0m: \033[35m%(funcName)s\033[0m: %(message)s"
    simple_format = "%(levelname)s:%(name)s %(message)s"

    # 配置日志处理器和格式化器
    handler = logging.StreamHandler()

    # 根据是否启用verbose模式设置不同的格式
    if args.verbose:
        handler.setFormatter(ColoredFormatter(verbose_format, datefmt="%I:%M%p"))
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
    else:
        handler.setFormatter(logging.Formatter(simple_format))
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

    logger.handlers = []  # 清除所有默认的处理器
    logger.addHandler(handler)


def resource_path(relative_path):
    """获取打包后资源文件的绝对路径"""
    if hasattr(sys, "_MEIPASS"):
        # 如果是打包后的环境
        base_path = sys._MEIPASS
    else:
        # 开发环境，直接使用当前路径
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    args = parse_args()

    # Check if OpenVPN is installed
    if not shutil.which("openvpn"):
        addOpenVPNtoSysPath()
        if not shutil.which("openvpn"):
            print(get_text("openvpn_not_installed"))
            exit(1)

    if not isAdmin() and is_windows:
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        return 1
    elif is_linux:
        if os.geteuid() != 0:
            print(get_text("privileges_check"))
            return 1

    # 自定义输出格式
    customLogger()

    if args.ovpnfile:
        return single_vpn_main(args)
    else:
        return vpn_list_main(args)


if __name__ == "__main__":
    if is_windows:
        try:
            import colorama  # type: ignore
            colorama.init()
        except ImportError:
            print(get_text("colorama_not_found"))
    sys.exit(main())
