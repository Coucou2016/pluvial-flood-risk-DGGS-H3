from pathlib import Path

from PIL import Image, ImageDraw
from pdf2image import convert_from_path


BASE = Path(__file__).resolve().parent / "qa_review_docx_v2"
PDF = BASE / "review_report_word_render.pdf"
PAGES = BASE / "pages"
PAGES.mkdir(parents=True, exist_ok=True)

images = convert_from_path(
    PDF,
    dpi=160,
    fmt="png",
    thread_count=8,
    poppler_path=r"C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin",
)
for i, im in enumerate(images, 1):
    im.save(PAGES / f"page-{i:02d}.png")

thumb_w = 500
thumb_h = int(images[0].height * thumb_w / images[0].width)
for start in range(0, len(images), 4):
    batch = images[start : start + 4]
    sheet = Image.new("RGB", (thumb_w * 2 + 60, (thumb_h + 45) * 2 + 30), "#d8d8d8")
    draw = ImageDraw.Draw(sheet)
    for j, im in enumerate(batch):
        page_no = start + j + 1
        thumb = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = 20 + (j % 2) * (thumb_w + 20)
        y = 25 + (j // 2) * (thumb_h + 45)
        sheet.paste(thumb, (x, y))
        draw.text((x, y - 18), f"Page {page_no}", fill="black")
    sheet.save(BASE / f"contact-{start + 1:02d}-{min(start + 4, len(images)):02d}.png")

print(f"pages={len(images)}")
