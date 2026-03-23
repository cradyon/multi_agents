#!/usr/bin/env python3

from __future__ import annotations

import math
import subprocess
from pathlib import Path


FONT = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    "=": ["00000", "11111", "00000", "11111", "00000", "00000", "00000"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00001", "00001", "00001", "00001", "10001", "10001", "01110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


class Canvas:
    def __init__(self, width: int, height: int, background: tuple[int, int, int]) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(background * width * height)

    def set_px(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i : i + 3] = bytes(color)

    def fill_rect(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int]) -> None:
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(self.width, x2)
        y2 = min(self.height, y2)
        if x2 <= x1 or y2 <= y1:
            return
        for y in range(y1, y2):
            row = (y * self.width + x1) * 3
            self.pixels[row : row + (x2 - x1) * 3] = bytes(color) * (x2 - x1)

    def draw_rect(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int], border: int = 4) -> None:
        self.fill_rect(x1, y1, x2, y1 + border, color)
        self.fill_rect(x1, y2 - border, x2, y2, color)
        self.fill_rect(x1, y1, x1 + border, y2, color)
        self.fill_rect(x2 - border, y1, x2, y2, color)

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int], thickness: int = 4) -> None:
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        while True:
            for ox in range(-thickness // 2, thickness // 2 + 1):
                for oy in range(-thickness // 2, thickness // 2 + 1):
                    self.set_px(x1 + ox, y1 + oy, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    def draw_arrow(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int]) -> None:
        self.draw_line(x1, y1, x2, y2, color, thickness=5)
        angle = math.atan2(y2 - y1, x2 - x1)
        for side in (-1, 1):
            tip_angle = angle + side * 2.45
            hx = int(x2 + 20 * math.cos(tip_angle))
            hy = int(y2 + 20 * math.sin(tip_angle))
            self.draw_line(x2, y2, hx, hy, color, thickness=5)

    def draw_text(self, x: int, y: int, text: str, color: tuple[int, int, int], scale: int = 4, center: bool = False) -> None:
        text = text.upper()
        glyph_w = 5 * scale
        gap = scale
        width = len(text) * (glyph_w + gap) - gap if text else 0
        if center:
            x -= width // 2
        cursor_x = x
        for ch in text:
            glyph = FONT.get(ch, FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        self.fill_rect(
                            cursor_x + gx * scale,
                            y + gy * scale,
                            cursor_x + (gx + 1) * scale,
                            y + (gy + 1) * scale,
                            color,
                        )
            cursor_x += glyph_w + gap

    def save_ppm(self, path: Path) -> None:
        path.write_bytes(f"P6\n{self.width} {self.height}\n255\n".encode() + self.pixels)


def draw_badge(canvas: Canvas, x: int, y: int, text: str) -> None:
    badge_w = max(220, len(text) * 16 + 24)
    canvas.fill_rect(x, y, x + badge_w, y + 44, (255, 255, 255))
    canvas.draw_rect(x, y, x + badge_w, y + 44, (144, 151, 170), border=3)
    canvas.draw_text(x + badge_w // 2, y + 10, text, (76, 86, 106), scale=2, center=True)


def draw_node(canvas: Canvas, box: tuple[int, int, int, int], fill: tuple[int, int, int], title: str, subtitle: str | None = None) -> None:
    x1, y1, x2, y2 = box
    canvas.fill_rect(x1, y1, x2, y2, fill)
    canvas.draw_rect(x1, y1, x2, y2, (58, 66, 86), border=5)
    canvas.draw_text((x1 + x2) // 2, y1 + 18, title, (34, 39, 52), scale=4, center=True)
    if subtitle:
        canvas.draw_text((x1 + x2) // 2, y1 + 56, subtitle, (68, 76, 94), scale=2, center=True)


def render_current(canvas: Canvas) -> None:
    nodes = {
        "START": (680, 70, 920, 150, (230, 201, 168)),
        "PLANNER": (620, 220, 980, 320, (214, 227, 255)),
        "RESEARCHER": (200, 430, 620, 530, (215, 242, 221)),
        "EXECUTOR": (980, 430, 1400, 530, (255, 233, 194)),
        "SYNTHESIZER": (620, 650, 980, 750, (233, 220, 255)),
        "END": (680, 800, 920, 880, (230, 201, 168)),
    }
    draw_node(canvas, nodes["START"][:4], nodes["START"][4], "START")
    draw_node(canvas, nodes["PLANNER"][:4], nodes["PLANNER"][4], "PLANNER", "MODE AND PLAN")
    draw_node(canvas, nodes["RESEARCHER"][:4], nodes["RESEARCHER"][4], "RESEARCHER", "CONTEXT")
    draw_node(canvas, nodes["EXECUTOR"][:4], nodes["EXECUTOR"][4], "EXECUTOR", "IMPLEMENT")
    draw_node(canvas, nodes["SYNTHESIZER"][:4], nodes["SYNTHESIZER"][4], "SYNTHESIZER", "MERGE")
    draw_node(canvas, nodes["END"][:4], nodes["END"][4], "END")
    canvas.draw_text(800, 24, "CURRENT WORKFLOW", (44, 52, 68), scale=4, center=True)

    canvas.draw_arrow(800, 150, 800, 220, (84, 95, 120))
    canvas.draw_arrow(720, 320, 430, 430, (84, 95, 120))
    canvas.draw_arrow(900, 320, 1160, 430, (84, 95, 120))
    canvas.draw_arrow(410, 530, 720, 650, (84, 95, 120))
    canvas.draw_arrow(1170, 530, 880, 650, (84, 95, 120))
    canvas.draw_arrow(800, 750, 800, 800, (84, 95, 120))

    draw_badge(canvas, 180, 340, "MODE = RESEARCH_ONLY")
    draw_badge(canvas, 970, 340, "MODE = EXECUTE_ONLY")
    draw_badge(canvas, 120, 385, "MODE = RESEARCH_THEN_EXECUTE")
    draw_badge(canvas, 240, 575, "RESEARCH_ONLY")
    draw_badge(canvas, 970, 575, "RESEARCH_THEN_EXECUTE")


def render_future(canvas: Canvas) -> None:
    nodes = {
        "START": (680, 60, 920, 140, (230, 201, 168)),
        "PLANNER": (620, 180, 980, 280, (214, 227, 255)),
        "A": (70, 380, 350, 480, (220, 236, 255)),
        "B": (440, 380, 720, 480, (215, 242, 221)),
        "C": (810, 380, 1090, 480, (255, 233, 194)),
        "D": (1180, 380, 1460, 480, (255, 222, 235)),
        "JOIN": (620, 620, 980, 720, (233, 220, 255)),
        "END": (680, 800, 920, 880, (230, 201, 168)),
    }
    canvas.draw_text(800, 20, "FUTURE PARALLEL WORKFLOW", (44, 52, 68), scale=4, center=True)
    draw_node(canvas, nodes["START"][:4], nodes["START"][4], "START")
    draw_node(canvas, nodes["PLANNER"][:4], nodes["PLANNER"][4], "PLANNER", "SPLIT WORK")
    draw_node(canvas, nodes["A"][:4], nodes["A"][4], "AGENT A", "ARCH")
    draw_node(canvas, nodes["B"][:4], nodes["B"][4], "AGENT B", "RESEARCH")
    draw_node(canvas, nodes["C"][:4], nodes["C"][4], "AGENT C", "EXECUTE")
    draw_node(canvas, nodes["D"][:4], nodes["D"][4], "AGENT D", "SYNTH PREP")
    draw_node(canvas, nodes["JOIN"][:4], nodes["JOIN"][4], "SYNTHESIZER", "JOIN RESULTS")
    draw_node(canvas, nodes["END"][:4], nodes["END"][4], "END")

    canvas.draw_arrow(800, 140, 800, 180, (84, 95, 120))
    for x in (210, 580, 950, 1320):
        canvas.draw_arrow(800, 280, x, 380, (84, 95, 120))
    canvas.draw_arrow(210, 480, 700, 620, (84, 95, 120))
    canvas.draw_arrow(580, 480, 760, 620, (84, 95, 120))
    canvas.draw_arrow(950, 480, 840, 620, (84, 95, 120))
    canvas.draw_arrow(1320, 480, 920, 620, (84, 95, 120))
    canvas.draw_arrow(800, 720, 800, 800, (84, 95, 120))
    draw_badge(canvas, 570, 315, "PARALLEL FAN OUT")
    draw_badge(canvas, 675, 750, "JOIN AND MERGE")


def render_image(name: str, mode: str) -> None:
    root = Path(__file__).resolve().parents[2]
    docs = root / "APP_DEMO" / "workflows"
    docs.mkdir(exist_ok=True)
    canvas = Canvas(1600, 900, (245, 244, 240))
    if mode == "current":
        render_current(canvas)
    else:
        render_future(canvas)
    ppm_path = docs / f"{name}.ppm"
    jpg_path = docs / f"{name}.jpg"
    canvas.save_ppm(ppm_path)
    subprocess.run(["sips", "-s", "format", "jpeg", str(ppm_path), "--out", str(jpg_path)], check=True)


def main() -> int:
    render_image("workflow-current", "current")
    render_image("workflow-future-parallel", "future")
    print("Wrote APP_DEMO/workflows/workflow-current.jpg")
    print("Wrote APP_DEMO/workflows/workflow-future-parallel.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
