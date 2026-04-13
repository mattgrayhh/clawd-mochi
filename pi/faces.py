"""
Face animations — normal eyes, squish eyes, logo reveal.
All drawing is done to display.draw (Pillow ImageDraw) then pushed via display.push_frame().
"""

import time
from config import (
    DISP_W, CONTENT_H, Y_OFFSET,
    EYE_W, EYE_H, EYE_GAP, EYE_OX, EYE_OY,
    C_ORANGE, C_BLACK, C_WHITE, C_DARKBG, C_MUTED, C_GREEN,
    LOGO_CX, LOGO_CY,
)
from logo_data import LOGO_TRIS, LOGO_SEGS


def _eye_lx(ox=0):
    return (DISP_W - (EYE_W * 2 + EYE_GAP)) // 2 + EYE_OX + ox


def _eye_rx(ox=0):
    return _eye_lx(ox) + EYE_W + EYE_GAP


def _eye_y():
    return (CONTENT_H - EYE_H) // 2 - EYE_OY


def _eye_cy():
    return _eye_y() + EYE_H // 2


def _cy(y):
    """Translate y from 240x240 content space to 240x280 display space."""
    return y + Y_OFFSET


def draw_normal_eyes(display, bg_color, ox=0, blink=False):
    """Draw square pixel eyes, optionally shifted horizontally or blinking."""
    display.fill_content(bg_color)
    d = display.draw
    lx, rx, ey = _eye_lx(ox), _eye_rx(ox), _eye_y()
    if not blink:
        d.rectangle([lx, _cy(ey), lx + EYE_W, _cy(ey + EYE_H)], fill=C_BLACK)
        d.rectangle([rx, _cy(ey), rx + EYE_W, _cy(ey + EYE_H)], fill=C_BLACK)
    else:
        d.rectangle([lx, _cy(ey + EYE_H // 2 - 3), lx + EYE_W, _cy(ey + EYE_H // 2 + 3)], fill=C_BLACK)
        d.rectangle([rx, _cy(ey + EYE_H // 2 - 3), rx + EYE_W, _cy(ey + EYE_H // 2 + 3)], fill=C_BLACK)
    display.push_frame()


def _draw_chevron(d, cx, cy, arm, reach, thk, right_facing, col):
    """Draw a chevron shape (> or <) with thickness."""
    for t in range(-thk, thk + 1):
        if right_facing:
            d.line([(cx - reach // 2, cy - arm + t), (cx + reach // 2, cy + t)], fill=col, width=1)
            d.line([(cx + reach // 2, cy + t), (cx - reach // 2, cy + arm + t)], fill=col, width=1)
        else:
            d.line([(cx + reach // 2, cy - arm + t), (cx - reach // 2, cy + t)], fill=col, width=1)
            d.line([(cx - reach // 2, cy + t), (cx + reach // 2, cy + arm + t)], fill=col, width=1)


def draw_squish_eyes(display, bg_color, closed=False):
    """Draw happy squint chevron eyes."""
    display.fill_content(bg_color)
    d = display.draw
    lx, rx = _eye_lx(0), _eye_rx(0)
    cy = _cy(_eye_cy())
    arm = EYE_H // 2
    reach = EYE_W // 2
    lcx = lx + EYE_W // 2
    rcx = rx + EYE_W // 2
    if not closed:
        _draw_chevron(d, lcx, cy, arm, reach, 10, True, C_BLACK)
        _draw_chevron(d, rcx, cy, arm, reach, 10, False, C_BLACK)
    else:
        d.rectangle([lx, cy - 5, lx + EYE_W, cy + 5], fill=C_BLACK)
        d.rectangle([rx, cy - 5, rx + EYE_W, cy + 5], fill=C_BLACK)
    display.push_frame()


def anim_normal_eyes(display, bg_color, speed_ms):
    """Normal eyes animation: wiggle left/right then double blink."""
    offsets = [-16, 16, -16, 16, 0]
    for ox in offsets:
        draw_normal_eyes(display, bg_color, ox=ox)
        time.sleep(speed_ms(80) / 1000.0)
    draw_normal_eyes(display, bg_color, blink=True)
    time.sleep(speed_ms(100) / 1000.0)
    draw_normal_eyes(display, bg_color, blink=False)
    time.sleep(speed_ms(70) / 1000.0)
    draw_normal_eyes(display, bg_color, blink=True)
    time.sleep(speed_ms(70) / 1000.0)
    draw_normal_eyes(display, bg_color, blink=False)


def anim_squish_eyes(display, bg_color, speed_ms):
    """Squish eyes animation: open/close 3 times."""
    for _ in range(3):
        draw_squish_eyes(display, bg_color, closed=False)
        time.sleep(speed_ms(160) / 1000.0)
        draw_squish_eyes(display, bg_color, closed=True)
        time.sleep(speed_ms(100) / 1000.0)
    draw_squish_eyes(display, bg_color, closed=False)


def draw_logo_filled(display, bg_color, fg_color):
    """Draw the Clawd logo filled with triangles."""
    display.fill_content(bg_color)
    d = display.draw
    for tri in LOGO_TRIS:
        x1, y1, x2, y2, x3, y3 = tri
        d.polygon(
            [(x1, _cy(y1)), (x2, _cy(y2)), (x3, _cy(y3))],
            fill=fg_color,
        )
    # "Anthropic" text below logo
    font = display.font_medium
    d.text((LOGO_CX - 45, _cy(210)), "Anthropic", fill=fg_color, font=font)
    display.push_frame()


def anim_logo_reveal(display, bg_color, speed_ms):
    """Stroke-by-stroke logo reveal animation."""
    display.fill_content(bg_color)
    d = display.draw
    for i, seg in enumerate(LOGO_SEGS):
        x1, y1, x2, y2 = seg
        d.line([(x1, _cy(y1)), (x2, _cy(y2))], fill=C_WHITE, width=2)
        if i % 4 == 0:
            display.push_frame()
            time.sleep(speed_ms(8) / 1000.0)
    # Final filled logo
    draw_logo_filled(display, bg_color, C_WHITE)
    time.sleep(1.5)


def draw_code_view(display):
    """Draw the 'Claude Code' splash screen."""
    display.fill_content(C_DARKBG)
    d = display.draw
    # Orange bars top and bottom
    d.rectangle([0, _cy(0), DISP_W, _cy(4)], fill=C_ORANGE)
    d.rectangle([0, _cy(CONTENT_H - 4), DISP_W, _cy(CONTENT_H)], fill=C_ORANGE)
    # "Claude" in orange
    d.text(((DISP_W - 144) // 2, _cy(CONTENT_H // 2 - 52)),
           "Claude", fill=C_ORANGE, font=display.font_xlarge)
    # "Code" in white
    d.text(((DISP_W - 96) // 2, _cy(CONTENT_H // 2 + 8)),
           "Code", fill=C_WHITE, font=display.font_xlarge)
    # Orange underline
    d.rectangle([(DISP_W - 96) // 2, _cy(CONTENT_H // 2 + 52),
                 (DISP_W - 96) // 2 + 96, _cy(CONTENT_H // 2 + 55)], fill=C_ORANGE)
    display.push_frame()


def draw_wifi_info(display, ssid, password, ip, mode="AP"):
    """Draw the WiFi connection info screen."""
    display.fill_content(C_DARKBG)
    d = display.draw
    d.rectangle([0, _cy(0), DISP_W, _cy(4)], fill=C_ORANGE)

    y = 16
    d.text((12, _cy(y)), f"WiFi: {ssid}", fill=C_WHITE, font=display.font_medium)
    y += 28
    d.text((12, _cy(y)), f"password: {password}", fill=C_MUTED, font=display.font_small)
    y += 24
    d.text((12, _cy(y)), "Open browser:", fill=C_WHITE, font=display.font_medium)
    y += 26
    d.text((12, _cy(y)), ip, fill=C_ORANGE, font=display.font_medium)
    y += 30
    d.text((12, _cy(y)), f"mode: {mode}", fill=C_MUTED, font=display.font_small)
    y += 16
    d.text((12, _cy(y)), "press button to start", fill=C_MUTED, font=display.font_small)
    display.push_frame()


def draw_boot_splash(display, bg_color):
    """Draw the boot splash with 'Clawd Mochi' text."""
    display.fill_content(bg_color)
    d = display.draw
    d.text((DISP_W // 2 - 54, _cy(CONTENT_H // 2 - 22)),
           "Clawd", fill=C_WHITE, font=display.font_xlarge)
    d.text((DISP_W // 2 - 54, _cy(CONTENT_H // 2 + 14)),
           "Mochi", fill=C_WHITE, font=display.font_xlarge)
    display.push_frame()
