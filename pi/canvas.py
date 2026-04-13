"""
Canvas mode — draw on the display from the web UI.
"""

from config import DISP_W, CONTENT_H, Y_OFFSET


class Canvas:
    """Manages the drawing canvas on the display."""

    def __init__(self, display):
        self.display = display
        self.active = False

    def _cy(self, y):
        return y + Y_OFFSET

    def clear(self, bg_color):
        self.display.fill_content(bg_color)
        self.display.push_frame()

    def draw_stroke(self, points, pen_color):
        """Draw a stroke from a list of (x, y) tuples with the given pen color."""
        d = self.display.draw
        prev = None
        for x, y in points:
            dy = self._cy(y)
            if prev is not None:
                d.line([prev, (x, dy)], fill=pen_color, width=3)
            else:
                d.ellipse([x - 2, dy - 2, x + 2, dy + 2], fill=pen_color)
            prev = (x, dy)
        self.display.push_frame()

    def activate(self, bg_color):
        self.active = True
        self.clear(bg_color)

    def deactivate(self):
        self.active = False
