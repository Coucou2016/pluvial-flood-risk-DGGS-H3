"""Encode text files as PNG bitmaps (3 payload bytes per pixel RGB) so the
browser can read them back via canvas and rebuild File objects."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".upload_chunks" / "encoded"
OUT.mkdir(parents=True, exist_ok=True)

files = {
    "manuscript.md": ROOT / "docs/paper/manuscript.md",
    "audit.md": ROOT / "docs/paper/audit.md",
    "reference_paper.md": ROOT / "1-s2.0-S2212420926001032-main.md",
    "chatgpt_context_W11.md": ROOT / "artifacts/chatgpt_context_W11.md",
}

WIDTH = 200


def encode_png(data: bytes) -> Image.Image:
    n = 8 + len(data)
    height = (n + WIDTH * 3 - 1) // (WIDTH * 3)
    total = WIDTH * height * 3
    payload = bytearray(total)
    payload[0:8] = struct.pack("<Q", len(data))
    payload[8 : 8 + len(data)] = data
    img = Image.new("RGB", (WIDTH, height))
    px = img.load()
    for i in range(0, total, 3):
        x = (i // 3) % WIDTH
        y = (i // 3) // WIDTH
        px[x, y] = (payload[i], payload[i + 1], payload[i + 2])
    return img


for name, path in files.items():
    img = encode_png(path.read_bytes())
    target = OUT / f"{name}.png"
    img.save(target, "PNG")
    print(f"{name}: {path.stat().st_size} bytes -> {target} ({img.size[0]}x{img.size[1]})")
