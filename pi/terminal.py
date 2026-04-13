"""
Terminal mode — pseudo-terminal display on the Whisplay HAT.
"""

from config import (
    DISP_W, CONTENT_H, Y_OFFSET,
    TERM_COLS, TERM_ROWS, TERM_CHAR_W, TERM_CHAR_H,
    TERM_PAD_X, TERM_PAD_Y, PREFIX_PX,
    C_DARKBG, C_ORANGE, C_WHITE, C_GREEN,
)


class Terminal:
    """Manages the terminal display state and rendering."""

    def __init__(self, display):
        self.display = display
        self.lines = [""] * TERM_ROWS
        self.row = 0
        self.col = 0
        self.active = False

    def _cy(self, y):
        return y + Y_OFFSET

    def clear(self):
        self.lines = [""] * TERM_ROWS
        self.row = 0
        self.col = 0

    def _draw_header(self):
        d = self.display.draw
        d.rectangle([0, self._cy(0), DISP_W, self._cy(TERM_PAD_Y + 1)], fill=C_DARKBG)
        d.text((TERM_PAD_X, self._cy(4)), "clawd@mochi terminal",
               fill=C_ORANGE, font=self.display.font_small)
        d.line([(0, self._cy(TERM_PAD_Y)), (DISP_W, self._cy(TERM_PAD_Y))], fill=C_ORANGE)

    def _draw_prefix(self, yy):
        d = self.display.draw
        d.text((TERM_PAD_X, self._cy(yy + 6)), "clawd:~$ ",
               fill=C_GREEN, font=self.display.font_small)

    def _draw_line(self, r):
        d = self.display.draw
        yy = TERM_PAD_Y + 4 + r * TERM_CHAR_H
        d.rectangle([0, self._cy(yy), DISP_W, self._cy(yy + TERM_CHAR_H)], fill=C_DARKBG)

        # Show prefix only on the active cursor line
        if r == self.row:
            self._draw_prefix(yy)

        # Draw text
        base_x = TERM_PAD_X + PREFIX_PX
        d.text((base_x, self._cy(yy + 1)), self.lines[r],
               fill=C_WHITE, font=self.display.font_medium)

        # Draw cursor on current row
        if r == self.row:
            cx = base_x + self.col * TERM_CHAR_W
            d.rectangle([cx, self._cy(yy + 1),
                         cx + TERM_CHAR_W - 2, self._cy(yy + TERM_CHAR_H - 1)],
                        fill=C_GREEN)

    def full_redraw(self):
        self.display.fill_content(C_DARKBG)
        self._draw_header()
        for r in range(TERM_ROWS):
            self._draw_line(r)
        self.display.push_frame()

    def _scroll(self):
        for i in range(TERM_ROWS - 1):
            self.lines[i] = self.lines[i + 1]
        self.lines[TERM_ROWS - 1] = ""
        self.row = TERM_ROWS - 1
        self.full_redraw()

    def add_char(self, c):
        if c in ('\n', '\r'):
            self.row += 1
            self.col = 0
            if self.row >= TERM_ROWS:
                self._scroll()
                return
            self._draw_line(self.row)
            self.display.push_frame()
        elif c in ('\b', chr(127)):
            if self.col > 0:
                self.col -= 1
                self.lines[self.row] = self.lines[self.row][:-1]
                self._draw_line(self.row)
                self.display.push_frame()
        elif 32 <= ord(c) < 127:
            if self.col >= TERM_COLS:
                self.row += 1
                self.col = 0
                if self.row >= TERM_ROWS:
                    self._scroll()
                    return
            if self.col == 0:
                yy = TERM_PAD_Y + 4 + self.row * TERM_CHAR_H
                self._draw_prefix(yy)
            self.lines[self.row] += c
            self.col += 1
            self._draw_line(self.row)
            self.display.push_frame()

    def activate(self):
        self.active = True
        self.clear()
        self.full_redraw()

    def deactivate(self):
        self.active = False
