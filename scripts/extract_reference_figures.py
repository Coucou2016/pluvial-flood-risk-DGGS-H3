"""Extract embedded images from the reference paper PDF for ChatGPT visual review.

Writes each raster image to artifacts/reference_paper_figures/img_<page>_<idx>.png
and prints a manifest with page number and pixel dimensions so we can map
extracted images to Fig 1-6 in the manuscript text.
"""
from __future__ import annotations

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "1-s2.0-S2212420926001032-main.pdf"
OUT = ROOT / "artifacts" / "reference_paper_figures"

OUT.mkdir(parents=True, exist_ok=True)

doc = pymupdf.open(PDF)
manifest = []
for page_no in range(len(doc)):
    page = doc[page_no]
    images = page.get_images(full=True)
    for idx, img in enumerate(images):
        xref = img[0]
        pix = pymupdf.Pixmap(doc, xref)
        if pix.n - pix.alpha >= 4:  # CMYK -> RGB
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        name = f"img_p{page_no + 1:02d}_{idx:02d}.png"
        out_path = OUT / name
        pix.save(out_path)
        manifest.append((name, page_no + 1, pix.width, pix.height, pix.n))
        print(f"{name}  page={page_no + 1}  {pix.width}x{pix.height}  n={pix.n}")

print(f"\nTotal images extracted: {len(manifest)} -> {OUT}")

# Also render each page's figure regions as full-page PNGs at moderate DPI,
# so ChatGPT can see figures in context with captions.
page_dir = OUT / "pages"
page_dir.mkdir(parents=True, exist_ok=True)
for page_no in range(len(doc)):
    page = doc[page_no]
    # find image blocks to skip text-only pages
    imgs = page.get_images(full=True)
    if not imgs:
        continue
    pix = page.get_pixmap(dpi=150)
    p = page_dir / f"page_{page_no + 1:02d}.png"
    pix.save(p)
    print(f"page render {p.name}")
