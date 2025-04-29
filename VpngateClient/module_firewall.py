import logging
import subprocess

# IPv4 防火墙规则
IPv4_COMMANDS = [
    # accept connections to loopback device
    ["iptables", "--append", "INPUT", "--in-interface", "lo", "--jump", "ACCEPT"],
    # accept connections from loopback device
    ["iptables", "--append", "OUTPUT", "--out-interface", "lo", "--jump", "ACCEPT"],
    # allow outbound broadcasts for dhcp traffic
    [
        "iptables",
        "--append",
        "OUTPUT",
        "--destination",
        "255.255.255.255",
        "--jump",
        "ACCEPT",
    ],
    # allow inbound broadcasts for dhcp traffic
    [
        "iptables",
        "--append",
        "INPUT",
        "--source",
        "255.255.255.255",
        "--jump",
        "ACCEPT",
    ],
    # allow inbound traffic from local network
    [
        "iptables",
        "--append",
        "INPUT",
        "--source",
        "192.168.0.0/16",
        "--destination",
        "192.168.0.0/16",
        "--jump",
        "ACCEPT",
    ],
    # allow outbound traffic to local network
    [
        "iptables",
        "--append",
        "OUTPUT",
        "--source",
        "192.168.0.0/16",
        "--destination",
        "192.168.0.0/16",
        "--jump",
        "ACCEPT",
    ],
    # allow packets to be forwarded from tun0 to other interfaces
    ["iptables", "--append", "FORWARD", "--out-interface", "tun+", "--jump", "ACCEPT"],
    # allow packets to be forwarded from any interface to tun0
    ["iptables", "--append", "FORWARD", "--in-interface", "tun+", "--jump", "ACCEPT"],
    # handle nated packets correctly
    [
        "iptables",
        "--table",
        "nat",
        "--append",
        "POSTROUTING",
        "--out-interface",
        "tun+",
        "--jump",
        "MASQUERADE",
    ],
    # drop packets not going to the VPN IP
    [
        "iptables",
        "--append",
        "OUTPUT",
        "!",
        "--out-interface",
        "tun+",
        "!",
        "--destination",
        "<IP>",
        "--jump",
        "DROP",
    ],
]

# IPv6 防火墙规则
IPv6_COMMANDS = [
    # drop inbound ipv6 packets
    ["ip6tables", "-P", "INPUT", "DROP"],
    # drop outbound ipv6 packets
    ["ip6tables", "-P", "OUTPUT", "DROP"],
    # drop forwarded ipv6 packets
    ["ip6tables", "-P", "FORWARD", "DROP"],
]


class FirewallManager:
    def __init__(self, ip, ipv4_commands=None, ipv6_commands=None):
        self.ip = ip
        self.ipv4_commands = ipv4_commands or IPv4_COMMANDS
        self.ipv6_commands = ipv6_commands or IPv6_COMMANDS
        self.log = logging.getLogger("FirewallManager")

    def setup_rules(self):
        """Sets up iptables rules for blocking traffic that's not going through the VPN."""
        self.log.info("Setting up iptables rules...")
        applied_rules = []

        try:
            for cmd_template in self.ipv4_commands:
                cmd = self._replace_ip(cmd_template)
                self._execute_command(cmd)
                applied_rules.append(cmd_template)

            for cmd_template in self.ipv6_commands:
                cmd = self._replace_ip(cmd_template)
                self._execute_command(cmd)
                applied_rules.append(cmd_template)

            self.log.info("iptables rules applied successfully.")
            return True
        except Exception as e:
            self.log.error(f"Failed to setup iptables: {e}")
            self.clear_rules(applied_rules)
            return False

    def clear_rules(self, rules_to_clear=None):
        """Clears iptables rules."""
        self.log.info("Clearing iptables rules...")
        rules = rules_to_clear or self.ipv4_commands + self.ipv6_commands

        for cmd_template in reversed(rules):
            cmd = self._replace_ip(cmd_template)
            cmd[cmd.index("--append")] = "--delete"
            try:
                self._execute_command(cmd)
            except Exception as e:
                self.log.warning(f"Failed to clear rule {cmd}: {e}")

    def _replace_ip(self, cmd_template):
        cmd = list(cmd_template)
        if "<IP>" in cmd:
            if not self.ip:
                raise ValueError("Missing VPN IP for iptables rule")
            cmd[cmd.index("<IP>")] = self.ip
        return cmd

    def _execute_command(self, cmd):
        self.log.debug(f"Executing command: {' '.join(cmd)}")
        subprocess.check_call(cmd)
