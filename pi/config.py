"""
Clawd Mochi — Raspberry Pi Zero 2W + Whisplay HAT
Configuration constants and shared state.
"""

# ── Display ───────────────────────────────────────────────────
DISP_W = 240
DISP_H = 280
# The original Arduino version used 240x240. We center content
# vertically on the 240x280 display with a 20px top offset.
CONTENT_H = 240
Y_OFFSET = (DISP_H - CONTENT_H) // 2  # 20px

# ── Eye constants ─────────────────────────────────────────────
EYE_W = 30
EYE_H = 60
EYE_GAP = 120
EYE_OX = 0
EYE_OY = 40

# ── Colours (RGB tuples) ─────────────────────────────────────
C_ORANGE = (218, 17, 0)
C_DARKBG = (10, 12, 16)
C_MUTED = (90, 88, 86)
C_GREEN = (80, 220, 130)
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)

# ── Terminal ──────────────────────────────────────────────────
TERM_COLS = 15
TERM_ROWS = 8
TERM_CHAR_W = 12
TERM_CHAR_H = 20
TERM_PAD_X = 8
TERM_PAD_Y = 18
PREFIX_PX = 54  # 9 chars x 6px

# ── Views ─────────────────────────────────────────────────────
VIEW_EYES_NORMAL = 0
VIEW_EYES_SQUISH = 1
VIEW_CODE = 2
VIEW_DRAW = 3

# ── WiFi ──────────────────────────────────────────────────────
AP_SSID = "ClaWD-Mochi"
AP_PASS = "clawd1234"
AP_IP = "192.168.4.1"
AP_SUBNET = "255.255.255.0"
AP_DHCP_START = "192.168.4.10"
AP_DHCP_END = "192.168.4.50"
WEB_PORT = 80

# ── WiFi config file (persisted across reboots) ──────────────
WIFI_CONFIG_PATH = "/etc/clawd-mochi/wifi.json"

# ── Sound effects ─────────────────────────────────────────────
SOUND_ENABLED = True
SOUND_VOLUME = 0.5

# ── Logo center ───────────────────────────────────────────────
LOGO_CX = 120
LOGO_CY = 105
