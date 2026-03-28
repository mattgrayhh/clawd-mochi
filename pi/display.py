"""
Display driver wrapper for the Whisplay HAT (ST7789V2, 240x280).
Uses Pillow for frame rendering and spidev for SPI communication.
"""

import time
import spidev
import gpiod
from PIL import Image, ImageDraw, ImageFont
from config import DISP_W, DISP_H, Y_OFFSET, CONTENT_H


# ── GPIO pin definitions (BCM numbering) ─────────────────────
DC_PIN = 27
RST_PIN = 4
BL_PIN = 22

# ── SPI settings ─────────────────────────────────────────────
SPI_BUS = 0
SPI_DEV = 0
SPI_SPEED = 60_000_000  # 60 MHz (conservative for Pi Zero 2W)


class Display:
    """Manages the Whisplay HAT ST7789V2 display."""

    def __init__(self):
        # GPIO setup using gpiod (modern Linux GPIO interface)
        self.chip = gpiod.Chip("gpiochip0")

        self.dc_line = self.chip.get_line(DC_PIN)
        self.rst_line = self.chip.get_line(RST_PIN)
        self.bl_line = self.chip.get_line(BL_PIN)

        self.dc_line.request(consumer="clawd-mochi", type=gpiod.LINE_REQ_DIR_OUT)
        self.rst_line.request(consumer="clawd-mochi", type=gpiod.LINE_REQ_DIR_OUT)
        self.bl_line.request(consumer="clawd-mochi", type=gpiod.LINE_REQ_DIR_OUT)

        # SPI setup
        self.spi = spidev.SpiDev()
        self.spi.open(SPI_BUS, SPI_DEV)
        self.spi.max_speed_hz = SPI_SPEED
        self.spi.mode = 0

        # Frame buffer — full 240x280 Pillow image
        self.frame = Image.new("RGB", (DISP_W, DISP_H), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.frame)

        # Try to load a monospace font for terminal text
        self._font_small = None
        self._font_medium = None
        self._font_large = None
        self._load_fonts()

        # Backlight state
        self.backlight_on = True

        # Initialize display hardware
        self._reset()
        self._init_display()
        self.set_backlight(True)

    def _load_fonts(self):
        """Load monospace fonts at various sizes."""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        ]
        font_path = None
        for fp in font_paths:
            try:
                ImageFont.truetype(fp, 12)
                font_path = fp
                break
            except (IOError, OSError):
                continue

        if font_path:
            self._font_small = ImageFont.truetype(font_path, 10)
            self._font_medium = ImageFont.truetype(font_path, 16)
            self._font_large = ImageFont.truetype(font_path, 24)
            self._font_xlarge = ImageFont.truetype(font_path, 36)
        else:
            self._font_small = ImageFont.load_default()
            self._font_medium = ImageFont.load_default()
            self._font_large = ImageFont.load_default()
            self._font_xlarge = ImageFont.load_default()

    def _reset(self):
        """Hardware reset the display."""
        self.rst_line.set_value(1)
        time.sleep(0.01)
        self.rst_line.set_value(0)
        time.sleep(0.01)
        self.rst_line.set_value(1)
        time.sleep(0.12)

    def _write_cmd(self, cmd):
        """Send a command byte to the display."""
        self.dc_line.set_value(0)
        self.spi.writebytes([cmd])

    def _write_data(self, data):
        """Send data bytes to the display."""
        self.dc_line.set_value(1)
        if isinstance(data, int):
            self.spi.writebytes([data])
        else:
            # Send in chunks (spidev has a transfer size limit)
            for i in range(0, len(data), 4096):
                self.spi.writebytes(data[i:i + 4096])

    def _init_display(self):
        """Initialize ST7789V2 registers."""
        # Sleep out
        self._write_cmd(0x11)
        time.sleep(0.12)

        # Memory data access control
        self._write_cmd(0x36)
        self._write_data(0x00)

        # Interface pixel format: 16-bit RGB565
        self._write_cmd(0x3A)
        self._write_data(0x05)

        # Porch setting
        self._write_cmd(0xB2)
        for b in [0x0C, 0x0C, 0x00, 0x33, 0x33]:
            self._write_data(b)

        # Gate control
        self._write_cmd(0xB7)
        self._write_data(0x35)

        # VCOM setting
        self._write_cmd(0xBB)
        self._write_data(0x19)

        # LCM control
        self._write_cmd(0xC0)
        self._write_data(0x2C)

        # VDV and VRH command enable
        self._write_cmd(0xC2)
        self._write_data(0x01)

        # VRH set
        self._write_cmd(0xC3)
        self._write_data(0x12)

        # VDV set
        self._write_cmd(0xC4)
        self._write_data(0x20)

        # Frame rate control
        self._write_cmd(0xC6)
        self._write_data(0x0F)

        # Power control
        self._write_cmd(0xD0)
        self._write_data(0xA4)
        self._write_data(0xA1)

        # Positive gamma
        self._write_cmd(0xE0)
        for b in [0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54,
                   0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23]:
            self._write_data(b)

        # Negative gamma
        self._write_cmd(0xE1)
        for b in [0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44,
                   0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23]:
            self._write_data(b)

        # Display inversion on (ST7789 typically needs this)
        self._write_cmd(0x21)

        # Display on
        self._write_cmd(0x29)
        time.sleep(0.05)

    def _set_window(self, x0, y0, x1, y1):
        """Set the drawing window on the display."""
        self._write_cmd(0x2A)  # Column address
        for b in [x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]:
            self._write_data(b)
        self._write_cmd(0x2B)  # Row address
        for b in [y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]:
            self._write_data(b)
        self._write_cmd(0x2C)  # Memory write

    def set_backlight(self, on):
        """Toggle backlight (active LOW on Whisplay HAT)."""
        self.backlight_on = on
        self.bl_line.set_value(0 if on else 1)

    def push_frame(self):
        """Push the current Pillow frame buffer to the display."""
        self._set_window(0, 0, DISP_W - 1, DISP_H - 1)

        # Convert to RGB565
        pixels = self.frame.tobytes()
        buf = bytearray(DISP_W * DISP_H * 2)
        idx = 0
        for i in range(0, len(pixels), 3):
            r, g, b = pixels[i], pixels[i + 1], pixels[i + 2]
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            buf[idx] = rgb565 >> 8
            buf[idx + 1] = rgb565 & 0xFF
            idx += 2

        self.dc_line.set_value(1)
        for i in range(0, len(buf), 4096):
            self.spi.writebytes(buf[i:i + 4096])

    def fill(self, color):
        """Fill the entire display with a solid color."""
        self.draw.rectangle([0, 0, DISP_W, DISP_H], fill=color)

    def fill_content(self, color):
        """Fill only the 240x240 content area (centered on 240x280)."""
        self.draw.rectangle([0, 0, DISP_W, DISP_H], fill=(0, 0, 0))
        self.draw.rectangle([0, Y_OFFSET, DISP_W, Y_OFFSET + CONTENT_H], fill=color)

    def content_y(self, y):
        """Translate a y-coordinate from 240x240 space to display space."""
        return y + Y_OFFSET

    @property
    def font_small(self):
        return self._font_small

    @property
    def font_medium(self):
        return self._font_medium

    @property
    def font_large(self):
        return self._font_large

    @property
    def font_xlarge(self):
        return self._font_xlarge

    def cleanup(self):
        """Clean up GPIO and SPI resources."""
        self.set_backlight(False)
        self.dc_line.release()
        self.rst_line.release()
        self.bl_line.release()
        self.spi.close()
