"""Build a self-contained manuscript HTML + PDF with figures embedded inline.

Canonical text source: docs/paper/manuscript.md (unchanged).
Figures are injected as data:image/png;base64 at their first in-text reference.
PDF is printed via headless Chrome when available.

Usage:
    .venv\\Scripts\\python.exe scripts\\build_manuscript_html.py
"""
from __future__ import annotations

import base64
import html as htmllib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_paper_report_html import md_to_simple_html  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "paper"
FIG = PAPER / "figures"

# (png file, first-reference anchor text that appears verbatim in the markdown,
#  fig number). The figure block is inserted right after the paragraph whose
#  text ends with the anchor.
FIGURES = [
    ("workflow_schematic.png", "summarised in Fig. 1.", 1),
    ("spatial_maps.png", "predictive performance is assessed separately from the out-of-fold metrics reported in Section 4.2.", 2),
    ("spatial_cv_folds.png", "and is not interpreted in isolation.", 3),
    ("multi_resolution_spatial.png", "does not imply an absence of scale loss.", 4),
    ("resolution_effects.png", "Table 4 lists the full ladder.", 5),
    ("adaptive_ablation.png", "produces 3,933 mixed cells, compared with 6,909 cells for uniform R11 refinement (Fig. 6).", 6),
]


def b64_png(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def caption_map() -> dict[int, str]:
    """Extract full '**Figure N. ...** ...' captions from manuscript.md.

    The bold marker wraps only the figure number + short title; the descriptive
    text that follows on the same paragraph is part of the caption too.
    """
    md = (PAPER / "manuscript.md").read_text(encoding="utf-8")
    caps: dict[int, str] = {}
    for para in re.split(r"\n\s*\n", md):
        m = re.match(r"\*\*Figure (\d)\.\s*(.*?)\*\*\s*(.*)", para, re.DOTALL)
        if m:
            num = int(m.group(1))
            title = m.group(2).strip()
            rest = m.group(3).strip()
            caps[num] = (title + " " + rest).strip() if rest else title
    return caps


def figure_block(num: int, data: str, caption: str) -> str:
    return (
        f'<figure id="fig-{num}">'
        f'<img src="data:image/png;base64,{data}" alt="Figure {num}" '
        f'style="max-width:100%;height:auto;border:1px solid #ccc;"/>'
        f'<figcaption><strong>Figure {num}.</strong> {htmllib.escape(caption)}</figcaption>'
        f"</figure>"
    )


def inject_figure(body_html: str, anchor: str, block: str) -> str:
    # The anchor is a substring of a rendered paragraph; insert the figure
    # right after that paragraph's closing </p>.
    esc_anchor = htmllib.escape(anchor)
    idx = body_html.find(esc_anchor)
    if idx == -1:
        # Try unescaped (in case punctuation/entity differ)
        idx = body_html.find(anchor)
    if idx == -1:
        raise ValueError(f"anchor not found in rendered HTML: {anchor}")
    close = body_html.find("</p>", idx)
    if close == -1:
        raise ValueError(f"no </p> after anchor: {anchor}")
    return body_html[: close + 4] + "\n" + block + body_html[close + 4 :]


def chrome_path() -> str | None:
    for p in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        rf"{Path.home()}\AppData\Local\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ):
        if Path(p).exists():
            return p
    return shutil.which("chrome") or shutil.which("google-chrome")


def main() -> None:
    ms = (PAPER / "manuscript.md").read_text(encoding="utf-8")
    body = md_to_simple_html(ms)

    caps = caption_map()
    for png, anchor, num in FIGURES:
        block = figure_block(num, b64_png(FIG / png), caps.get(num, ""))
        body = inject_figure(body, anchor, block)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    css = """
:root { --ink:#1a1a1a; --muted:#555; --line:#ddd; --accent:#0b3d5c; }
* { box-sizing: border-box; }
body { font-family: "Times New Roman", Times, serif; color: var(--ink); line-height: 1.6; margin: 0; background: #fff; }
.wrap { max-width: 860px; margin: 0 auto; padding: 36px 28px 72px; }
h1 { font-size: 1.45rem; color: var(--accent); margin: 0 0 18px; line-height: 1.3; }
h2 { color: var(--accent); border-bottom: 1px solid var(--line); padding-bottom: 4px; margin-top: 2.2rem; font-size: 1.2rem; }
h3 { margin-top: 1.5rem; font-size: 1.05rem; }
h4 { margin-top: 1.2rem; color: #333; }
table { border-collapse: collapse; width: 100%; margin: 12px 0 8px; font-size: 0.9rem; }
th, td { border: 1px solid var(--line); padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: #eef3f7; }
figure { margin: 20px 0 26px; page-break-inside: avoid; }
figcaption { font-size: 0.9rem; color: #222; margin-top: 8px; line-height: 1.45; text-align: justify; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.86em; }
blockquote { border-left: 4px solid var(--accent); margin: 12px 0; padding: 6px 14px; background: #f3f7fb; }
pre.eq { background: #f7f7f7; padding: 10px 12px; overflow-x: auto; font-size: 0.92rem; }
hr { border: none; border-top: 1px solid var(--line); margin: 26px 0; }
ul, ol { margin: 8px 0 12px; }
a { color: var(--accent); }
@page { margin: 18mm 16mm; }
@media print { a { color: inherit; text-decoration: none; } .wrap { padding: 0; max-width: none; } }
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Manuscript — Spatially blocked pluvial flood learning on the H3 grid</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<div style="font-size:0.82rem;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:18px">
Self-contained manuscript · figures embedded (Base64) · generated {now}
</div>
{body}
</div>
</body>
</html>
"""

    out_html = PAPER / "manuscript.html"
    out_html.write_text(html, encoding="utf-8")
    print(f"wrote {out_html} ({out_html.stat().st_size} bytes)")

    chrome = chrome_path()
    if not chrome:
        print("Chrome/Edge not found; skipping PDF (HTML is authoritative).")
        return

    out_pdf = PAPER / "manuscript.pdf"
    url = out_html.resolve().as_uri()
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--print-to-pdf=" + str(out_pdf),
        url,
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    if r.returncode == 0 and out_pdf.exists():
        print(f"wrote {out_pdf} ({out_pdf.stat().st_size} bytes)")
    else:
        print(f"Chrome print failed (rc={r.returncode}); HTML is authoritative.")
        print(r.stderr.decode("utf-8", errors="replace")[:800])


if __name__ == "__main__":
    main()
