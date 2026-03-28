#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Clawd Mochi — Raspberry Pi Zero 2W + Whisplay HAT Setup
#
#  Run this script on a fresh Raspberry Pi OS installation:
#    chmod +x setup.sh && sudo ./setup.sh
# ═══════════════════════════════════════════════════════════════

set -e

INSTALL_DIR="/opt/clawd-mochi"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════════╗"
echo "  CLAWD MOCHI — Raspberry Pi Setup"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── Check for root ─────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo ./setup.sh)"
    exit 1
fi

# ── Enable SPI ─────────────────────────────────────────────
echo "[1/7] Enabling SPI..."
raspi-config nonint do_spi 0
echo "  SPI enabled."

# ── Enable I2C and I2S (for WM8960 audio) ─────────────────
echo "[2/7] Enabling I2C and I2S for audio..."

# Add to config.txt if not already present
CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_FILE="/boot/config.txt"
fi

grep -q "^dtparam=i2c_arm=on" "$CONFIG_FILE" || echo "dtparam=i2c_arm=on" >> "$CONFIG_FILE"
grep -q "^dtparam=i2s=on" "$CONFIG_FILE" || echo "dtparam=i2s=on" >> "$CONFIG_FILE"
grep -q "^dtoverlay=i2s-mmap" "$CONFIG_FILE" || echo "dtoverlay=i2s-mmap" >> "$CONFIG_FILE"

# Add kernel modules
grep -q "i2c-dev" /etc/modules || echo "i2c-dev" >> /etc/modules
grep -q "snd-soc-wm8960" /etc/modules || echo "snd-soc-wm8960" >> /etc/modules

echo "  I2C/I2S configured."

# ── Install WM8960 audio driver ────────────────────────────
echo "[3/7] Installing WM8960 audio driver..."
if [ ! -d "/tmp/whisplay-driver" ]; then
    git clone --depth 1 https://github.com/PiSugar/Whisplay.git /tmp/whisplay-driver 2>/dev/null || true
fi
if [ -f "/tmp/whisplay-driver/Driver/install_wm8960_drive.sh" ]; then
    cd /tmp/whisplay-driver/Driver
    bash install_wm8960_drive.sh || echo "  WARNING: WM8960 driver install had issues (may already be installed)"
    cd "$SCRIPT_DIR"
fi
echo "  Audio driver setup complete."

# ── Install system packages ────────────────────────────────
echo "[4/7] Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-pil \
    python3-spidev \
    python3-pygame \
    python3-flask \
    python3-gpiod \
    fonts-dejavu-core \
    hostapd \
    dnsmasq \
    2>/dev/null

echo "  System packages installed."

# ── Install Python packages ────────────────────────────────
echo "[5/7] Installing Python packages..."
pip3 install --break-system-packages -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null || \
    pip3 install -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null || \
    echo "  WARNING: pip install had issues (system packages should cover it)"
echo "  Python packages installed."

# ── Copy application files ─────────────────────────────────
echo "[6/7] Installing Clawd Mochi to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/sounds"
mkdir -p /etc/clawd-mochi

cp "$SCRIPT_DIR"/app.py "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/config.py "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/display.py "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/faces.py "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/logo_data.py "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/terminal.py "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/canvas.py "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/audio.py "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/wifi.py "$INSTALL_DIR/"
cp "$SCRIPT_DIR"/web.py "$INSTALL_DIR/"

echo "  Application installed."

# ── Install and enable systemd service ─────────────────────
echo "[7/7] Setting up systemd service..."
cp "$SCRIPT_DIR/clawd-mochi.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable clawd-mochi.service
echo "  Service enabled (will start on boot)."

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "  Setup complete!"
echo ""
echo "  Start now:  sudo systemctl start clawd-mochi"
echo "  View logs:  sudo journalctl -u clawd-mochi -f"
echo "  Stop:       sudo systemctl stop clawd-mochi"
echo ""
echo "  WiFi: ClaWD-Mochi (pw: clawd1234)"
echo "  URL:  http://192.168.4.1"
echo ""
echo "  A reboot is recommended for audio to work."
echo "  Run: sudo reboot"
echo "╚══════════════════════════════════════════════════╝"
