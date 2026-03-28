"""
WiFi manager — supports AP mode, client mode, and switching between them.
Uses NetworkManager (nmcli) which is standard on Raspberry Pi OS.
"""

import json
import os
import subprocess
import time

from config import AP_SSID, AP_PASS, AP_IP, WIFI_CONFIG_PATH


def _run(cmd, check=False):
    """Run a shell command and return stdout."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""


def _nmcli_available():
    """Check if NetworkManager (nmcli) is available."""
    return _run("which nmcli") != ""


class WiFiManager:
    """Manages WiFi in AP mode and client mode using NetworkManager."""

    def __init__(self):
        self.mode = "ap"  # "ap" or "client"
        self.client_ssid = None
        self.client_ip = None
        self._load_config()

    def _load_config(self):
        """Load saved WiFi config if it exists."""
        try:
            if os.path.exists(WIFI_CONFIG_PATH):
                with open(WIFI_CONFIG_PATH) as f:
                    cfg = json.load(f)
                    self.client_ssid = cfg.get("ssid")
                    return cfg
        except (json.JSONDecodeError, IOError):
            pass
        return {}

    def _save_config(self, ssid, password):
        """Save WiFi client config for persistence across reboots."""
        os.makedirs(os.path.dirname(WIFI_CONFIG_PATH), exist_ok=True)
        with open(WIFI_CONFIG_PATH, "w") as f:
            json.dump({"ssid": ssid, "password": password}, f)

    def start_ap(self):
        """Start WiFi in Access Point mode."""
        if not _nmcli_available():
            # Fallback: use hostapd + dnsmasq directly
            self._start_ap_legacy()
            return

        # Delete any existing AP connection, then create new one
        _run(f"sudo nmcli connection delete '{AP_SSID}' 2>/dev/null")
        _run(
            f"sudo nmcli connection add type wifi ifname wlan0 con-name '{AP_SSID}' "
            f"autoconnect no ssid '{AP_SSID}'"
        )
        _run(
            f"sudo nmcli connection modify '{AP_SSID}' "
            f"802-11-wireless.mode ap "
            f"802-11-wireless.band bg "
            f"ipv4.addresses {AP_IP}/24 "
            f"ipv4.method shared "
            f"wifi-sec.key-mgmt wpa-psk "
            f"wifi-sec.psk '{AP_PASS}'"
        )
        _run(f"sudo nmcli connection up '{AP_SSID}'")
        self.mode = "ap"
        time.sleep(2)

    def _start_ap_legacy(self):
        """Fallback AP mode using hostapd and dnsmasq config files."""
        hostapd_conf = f"""interface=wlan0
driver=nl80211
ssid={AP_SSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
wpa=2
wpa_passphrase={AP_PASS}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
"""
        dnsmasq_conf = f"""interface=wlan0
dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h
address=/#/{AP_IP}
"""
        os.makedirs("/tmp/clawd-mochi", exist_ok=True)
        with open("/tmp/clawd-mochi/hostapd.conf", "w") as f:
            f.write(hostapd_conf)
        with open("/tmp/clawd-mochi/dnsmasq.conf", "w") as f:
            f.write(dnsmasq_conf)

        _run("sudo rfkill unblock wlan")
        _run("sudo ip link set wlan0 down")
        _run(f"sudo ip addr flush dev wlan0")
        _run(f"sudo ip addr add {AP_IP}/24 dev wlan0")
        _run("sudo ip link set wlan0 up")
        _run("sudo killall hostapd 2>/dev/null; sudo killall dnsmasq 2>/dev/null")
        _run("sudo hostapd -B /tmp/clawd-mochi/hostapd.conf")
        _run("sudo dnsmasq -C /tmp/clawd-mochi/dnsmasq.conf")
        self.mode = "ap"
        time.sleep(2)

    def connect_to_wifi(self, ssid, password):
        """Connect to an existing WiFi network."""
        if not _nmcli_available():
            return self._connect_legacy(ssid, password)

        # Try to connect
        result = _run(
            f"sudo nmcli device wifi connect '{ssid}' password '{password}' ifname wlan0",
        )
        if "successfully" in result.lower() or "activated" in result.lower():
            self._save_config(ssid, password)
            self.mode = "client"
            self.client_ssid = ssid
            self.client_ip = self._get_ip()
            return True
        return False

    def _connect_legacy(self, ssid, password):
        """Fallback: connect using wpa_supplicant."""
        wpa_conf = f"""ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
        _run("sudo killall hostapd 2>/dev/null; sudo killall dnsmasq 2>/dev/null")
        with open("/tmp/clawd-mochi/wpa_supplicant.conf", "w") as f:
            f.write(wpa_conf)
        _run("sudo wpa_supplicant -B -i wlan0 -c /tmp/clawd-mochi/wpa_supplicant.conf")
        _run("sudo dhclient wlan0")
        time.sleep(5)

        ip = self._get_ip()
        if ip:
            self._save_config(ssid, password)
            self.mode = "client"
            self.client_ssid = ssid
            self.client_ip = ip
            return True
        # Failed — go back to AP mode
        self.start_ap()
        return False

    def _get_ip(self):
        """Get the current IP address of wlan0."""
        output = _run("ip -4 addr show wlan0 | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'")
        return output if output else None

    def get_ip(self):
        """Get the current IP address."""
        if self.mode == "ap":
            return AP_IP
        return self._get_ip() or AP_IP

    def scan_networks(self):
        """Scan for available WiFi networks."""
        if _nmcli_available():
            output = _run("sudo nmcli -t -f SSID,SIGNAL device wifi list ifname wlan0 --rescan yes")
        else:
            _run("sudo iwlist wlan0 scan > /dev/null 2>&1")
            output = _run("sudo iwlist wlan0 scan | grep -oP '(?<=ESSID:\").*(?=\")'")

        networks = []
        seen = set()
        for line in output.split("\n"):
            if not line.strip():
                continue
            parts = line.split(":")
            ssid = parts[0].strip()
            signal = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 0
            if ssid and ssid not in seen:
                seen.add(ssid)
                networks.append({"ssid": ssid, "signal": signal})
        networks.sort(key=lambda n: n["signal"], reverse=True)
        return networks

    def auto_connect(self):
        """Try to connect to saved WiFi, fall back to AP mode."""
        cfg = self._load_config()
        if cfg.get("ssid") and cfg.get("password"):
            if self.connect_to_wifi(cfg["ssid"], cfg["password"]):
                return True
        self.start_ap()
        return False

    def cleanup(self):
        """Clean up WiFi resources."""
        if self.mode == "ap" and not _nmcli_available():
            _run("sudo killall hostapd 2>/dev/null; sudo killall dnsmasq 2>/dev/null")
