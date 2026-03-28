#!/usr/bin/env python3
"""
Clawd Mochi — Raspberry Pi Zero 2W + Whisplay HAT
Main entry point. Initializes hardware, starts WiFi, and runs the web server.
"""

import signal
import sys
import time
import threading

from config import (
    VIEW_EYES_NORMAL, C_ORANGE, AP_SSID, AP_PASS, AP_IP,
    WEB_PORT, SOUND_ENABLED, SOUND_VOLUME,
)
from display import Display
from terminal import Terminal
from canvas import Canvas
from audio import Audio
from wifi import WiFiManager
from web import create_app
from faces import (
    draw_boot_splash, anim_logo_reveal, draw_normal_eyes,
    draw_wifi_info, anim_normal_eyes,
)


class Mochi:
    """Main application state — passed to the Flask routes."""

    def __init__(self):
        # State
        self.current_view = VIEW_EYES_NORMAL
        self.busy = False
        self.anim_speed = 1  # 1=slow, 2=normal, 3=fast
        self.anim_bg_color = C_ORANGE
        self.draw_bg_color = C_ORANGE

        # Hardware
        print("[clawd-mochi] Initializing display...")
        self.display = Display()

        print("[clawd-mochi] Initializing terminal...")
        self.terminal = Terminal(self.display)

        print("[clawd-mochi] Initializing canvas...")
        self.canvas = Canvas(self.display)

        print("[clawd-mochi] Initializing audio...")
        self.audio = Audio(enabled=SOUND_ENABLED, volume=SOUND_VOLUME)

        print("[clawd-mochi] Initializing WiFi...")
        self.wifi = WiFiManager()

        # Button state (Whisplay HAT button on BCM 17)
        self._setup_button()

    def speed_ms(self, ms):
        """Convert a base delay to speed-adjusted milliseconds."""
        if self.anim_speed == 3:
            return ms // 2
        if self.anim_speed == 1:
            return ms * 2
        return ms

    def _setup_button(self):
        """Set up the Whisplay HAT hardware button (BCM 17)."""
        try:
            import gpiod
            self._btn_chip = gpiod.Chip("gpiochip0")
            self._btn_line = self._btn_chip.get_line(17)
            self._btn_line.request(
                consumer="clawd-mochi-btn",
                type=gpiod.LINE_REQ_EV_RISING_EDGE,
            )
            self._btn_thread = threading.Thread(target=self._button_loop, daemon=True)
            self._btn_thread.start()
        except Exception as e:
            print(f"[clawd-mochi] Button setup failed (non-fatal): {e}")

    def _button_loop(self):
        """Poll the button for presses and cycle views."""
        while True:
            try:
                if self._btn_line.event_wait(sec=1):
                    self._btn_line.event_read()
                    self._on_button_press()
            except Exception:
                time.sleep(1)

    def _on_button_press(self):
        """Handle button press: cycle through views."""
        if self.busy:
            return
        self.audio.play("click")

        # Cycle: normal -> squish -> code -> normal
        view_cycle = {0: 1, 1: 2, 2: 0, 3: 0}
        next_view = view_cycle.get(self.current_view, 0)

        self.busy = True
        if next_view == 0:
            self.current_view = 0
            if self.terminal.active:
                self.terminal.deactivate()
            anim_normal_eyes(self.display, self.anim_bg_color, self.speed_ms)
        elif next_view == 1:
            self.current_view = 1
            from faces import anim_squish_eyes
            anim_squish_eyes(self.display, self.anim_bg_color, self.speed_ms)
        elif next_view == 2:
            self.current_view = 2
            from faces import draw_code_view
            draw_code_view(self.display)
            self.terminal.activate()
        self.busy = False

    def cleanup(self):
        """Clean up all resources."""
        print("[clawd-mochi] Shutting down...")
        self.display.cleanup()
        self.audio.cleanup()
        self.wifi.cleanup()


def main():
    mochi = Mochi()

    # Signal handler for clean shutdown
    def handle_signal(sig, frame):
        mochi.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # ── Boot sequence ─────────────────────────────────────────
    print("[clawd-mochi] Boot splash...")
    draw_boot_splash(mochi.display, mochi.anim_bg_color)
    mochi.audio.play("startup")
    time.sleep(1.2)

    print("[clawd-mochi] Logo reveal...")
    anim_logo_reveal(mochi.display, mochi.anim_bg_color, mochi.speed_ms)

    # ── Start WiFi ────────────────────────────────────────────
    print("[clawd-mochi] Starting WiFi...")
    connected = mochi.wifi.auto_connect()
    if connected:
        ip = mochi.wifi.get_ip()
        mode = "Client"
        ssid = mochi.wifi.client_ssid or "WiFi"
        print(f"[clawd-mochi] Connected to {ssid} at {ip}")
    else:
        ip = AP_IP
        mode = "AP"
        ssid = AP_SSID
        print(f"[clawd-mochi] AP mode: {AP_SSID} / {AP_PASS} -> {ip}")

    draw_wifi_info(mochi.display, ssid, AP_PASS if mode == "AP" else "****", ip, mode=mode)

    # ── Start web server ──────────────────────────────────────
    app = create_app(mochi)
    print(f"[clawd-mochi] Web server starting on port {WEB_PORT}...")
    print(f"[clawd-mochi] Open http://{ip} in your browser")

    try:
        # Use threaded=True so animations don't block HTTP requests
        app.run(host="0.0.0.0", port=WEB_PORT, threaded=True, debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        mochi.cleanup()


if __name__ == "__main__":
    main()
