# Clawd Mochi — Raspberry Pi Zero 2W + Whisplay HAT

A port of the [Clawd Mochi](../README.md) desk companion from ESP32-C3 to Raspberry Pi Zero 2W with the [PiSugar Whisplay HAT](https://www.pisugar.com/products/whisplay-hat-for-pi-zero-2w-audio-display).

## Hardware

- **Raspberry Pi Zero 2W**
- **PiSugar Whisplay HAT** (ST7789V2 240x280 LCD + WM8960 audio + button + RGB LED)

## Features

All original features, plus extras enabled by the Pi platform:

| Feature | Description |
|---------|-------------|
| Animated faces | Normal eyes (wiggle + blink), squish eyes (chevron open/close) |
| Claude Code logo | Stroke-by-stroke reveal animation |
| Terminal mode | Type from your phone, see it on the display |
| Canvas drawing | Draw on the display from the web UI |
| WiFi AP mode | Creates its own hotspot (ClaWD-Mochi / clawd1234) |
| WiFi client mode | Join your home WiFi via the config portal |
| Sound effects | Beeps/chirps on view switches and interactions |
| Hardware button | Press to cycle through views |
| Auto-start | Runs as a systemd service on boot |

## Quick Start

1. Flash **Raspberry Pi OS** (full, not Lite) to your SD card
2. Attach the Whisplay HAT to your Pi Zero 2W
3. SSH into the Pi and clone this repo:
   ```bash
   git clone https://github.com/mattgrayhh/clawd-mochi.git
   cd clawd-mochi/pi
   ```
4. Run the setup script:
   ```bash
   chmod +x setup.sh
   sudo ./setup.sh
   ```
5. Reboot (required for audio):
   ```bash
   sudo reboot
   ```
6. Connect your phone to the **ClaWD-Mochi** WiFi (password: `clawd1234`)
7. Open **http://192.168.4.1** in your browser

## WiFi Modes

The Pi starts in **AP mode** by default. Use the WiFi config button in the web UI to:
- Scan for nearby networks
- Connect to your home WiFi
- Switch back to AP mode

When connected to your home WiFi, access the controller at the Pi's IP address (shown on the display).

WiFi settings persist across reboots in `/etc/clawd-mochi/wifi.json`.

## Manual Control

```bash
# Start manually
sudo python3 /opt/clawd-mochi/app.py

# Service commands
sudo systemctl start clawd-mochi
sudo systemctl stop clawd-mochi
sudo systemctl restart clawd-mochi
sudo journalctl -u clawd-mochi -f   # View logs
```

## File Structure

```
pi/
├── app.py              # Main entry point
├── config.py           # Constants and configuration
├── display.py          # Whisplay HAT display driver (ST7789V2)
├── faces.py            # Face animations and drawing
├── logo_data.py        # Clawd logo triangle/segment data
├── terminal.py         # Terminal mode
├── canvas.py           # Drawing canvas mode
├── audio.py            # Sound effects (pygame.mixer)
├── wifi.py             # WiFi AP/client manager
├── web.py              # Flask web server and routes
├── requirements.txt    # Python dependencies
├── setup.sh            # One-step installation script
├── clawd-mochi.service # systemd unit file
└── sounds/             # Generated sound effect WAVs
```

## Display Differences

The Whisplay HAT has a **240x280** display (vs 240x240 on the original). Content is centered vertically with 20px padding top and bottom. The extra space is filled with black.
