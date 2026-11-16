#!/usr/bin/env python3
"""Genera los iconos PNG de la app usando solo la librería estándar.

Uso:  python tools/make-icons.py
Crea la carpeta icons/ con los distintos tamaños.
"""
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "icons"))

GREEN = (11, 122, 59)
WHITE = (255, 255, 255)


def inside_round_rect(px, py, x0, y0, x1, y1, r):
    cx = min(max(px, x0 + r), x1 - r)
    cy = min(max(py, y0 + r), y1 - r)
    dx = px - cx
    dy = py - cy
    return dx * dx + dy * dy <= r * r


def write_png(path, size, pixels):
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filtro None
        for x in range(size):
            r, g, b, a = pixels[y * size + x]
            raw += bytes((r, g, b, a))

    def chunk(typ, data):
        return (
            struct.pack(">I", len(data))
            + typ
            + data
            + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as fh:
        fh.write(png)


def render(size, maskable=False):
    """Dibuja una bolsa de la compra blanca con una lista dentro, sobre verde."""
    ss = 8 if size <= 64 else 3
    scale = 0.78 if maskable else 1.0

    bg_r = 0.0 if maskable else 0.22 * size

    bag_w = 0.50 * size * scale
    bag_h = 0.44 * size * scale
    bag_x0 = size / 2 - bag_w / 2
    bag_x1 = bag_x0 + bag_w
    bag_y0 = size * 0.58 - bag_h / 2
    bag_y1 = bag_y0 + bag_h
    bag_rr = 0.09 * size * scale

    h_cx = size / 2
    h_cy = bag_y0
    h_ro = 0.155 * size * scale
    h_ri = 0.105 * size * scale

    t = 0.045 * size * scale
    lx0 = bag_x0 + 0.10 * size * scale
    lx1 = lx0 + 0.24 * size * scale
    line_ys = [
        bag_y0 + bag_h * 0.30,
        bag_y0 + bag_h * 0.50,
        bag_y0 + bag_h * 0.70,
    ]

    def is_line(px, py):
        for ly in line_ys:
            if inside_round_rect(px, py, lx0, ly - t / 2, lx1, ly + t / 2, t / 2):
                return True
        return False

    def is_bag(px, py):
        return inside_round_rect(px, py, bag_x0, bag_y0, bag_x1, bag_y1, bag_rr)

    def is_handle(px, py):
        dx = px - h_cx
        dy = py - h_cy
        if dy > 0:
            return False
        d2 = dx * dx + dy * dy
        return h_ri * h_ri <= d2 <= h_ro * h_ro

    def is_bg(px, py):
        return inside_round_rect(px, py, 0.0, 0.0, float(size), float(size), bg_r)

    step = 1.0 / ss
    off = step / 2
    n = ss * ss
    pixels = []

    for y in range(size):
        for x in range(size):
            sr = sg = sb = 0
            sa = 0
            for sy in range(ss):
                py = y + off + sy * step
                for sx in range(ss):
                    px = x + off + sx * step
                    if is_bag(px, py) or is_handle(px, py):
                        color = GREEN if is_line(px, py) else WHITE
                    elif is_bg(px, py):
                        color = GREEN
                    else:
                        continue
                    sr += color[0]
                    sg += color[1]
                    sb += color[2]
                    sa += 1
            if sa == 0:
                pixels.append((0, 0, 0, 0))
            else:
                pixels.append(
                    (round(sr / sa), round(sg / sa), round(sb / sa), round(255 * sa / n))
                )
    return pixels


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    targets = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-512.png", 512, True),
        ("apple-touch-icon.png", 180, False),
        ("favicon-32.png", 32, False),
    ]
    for name, size, maskable in targets:
        path = os.path.join(OUT_DIR, name)
        write_png(path, size, render(size, maskable))
        print("creado", name, size, "x", size)


if __name__ == "__main__":
    main()
