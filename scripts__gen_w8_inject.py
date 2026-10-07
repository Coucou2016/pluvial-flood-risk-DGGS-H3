"""Generate W8 injection scripts: one JS per text file pushing a File object
into window.__injectFiles, then a finalize script that loads the two figure
PNGs from the local server, builds a DataTransfer, and replaces the files in
the ChatGPT upload input."""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".upload_chunks" / "w8"

TEXT_FILES = [
    "manuscript.md",
    "audit.md",
    "figures.py",
    "reference_paper.md",
    "report.md",
    "chatgpt_context_W7.md",
]
TEXT_SRC = {
    "manuscript.md": ROOT / "docs/paper/manuscript.md",
    "audit.md": ROOT / "docs/paper/audit.md",
    "figures.py": ROOT / "src/pluvial_flood_risk/figures.py",
    "reference_paper.md": ROOT / "1-s2.0-S2212420926001032-main.md",
    "report.md": ROOT / "docs/paper/report.md",
    "chatgpt_context_W7.md": ROOT / "artifacts/chatgpt_context_W7.md",
}
TEXT_TYPE = {
    "manuscript.md": "text/markdown",
    "audit.md": "text/markdown",
    "figures.py": "text/x-python",
    "reference_paper.md": "text/markdown",
    "report.md": "text/markdown",
    "chatgpt_context_W7.md": "text/markdown",
}
FIG_URLS = [
    "http://127.0.0.1:8973/docs/paper/figures/spatial_maps.png",
    "http://127.0.0.1:8973/docs/paper/figures/resolution_effects.png",
]

OUT.mkdir(parents=True, exist_ok=True)


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")


for name in TEXT_FILES:
    b64 = base64.b64encode(TEXT_SRC[name].read_bytes()).decode()
    js = (
        "(() => {\n"
        f"  const b64 = '{b64}';\n"
        "  const bin = atob(b64);\n"
        "  const arr = new Uint8Array(bin.length);\n"
        "  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);\n"
        "  window.__injectFiles = window.__injectFiles || [];\n"
        f"  window.__injectFiles.push(new File([arr], {esc(repr(name))}, {{ type: '{TEXT_TYPE[name]}' }}));\n"
        f"  return {esc(repr(name))} + ':ok(' + arr.length + ')';\n"
        "})()"
    )
    (OUT / f"inject_{name}.js").write_text(js, encoding="utf-8")
    print(f"inject_{name}.js: {len(js)} chars")

fig_urls_js = "[" + ", ".join(esc(repr(u)) for u in FIG_URLS) + "]"
finalize = (
    "(() => {\n"
    "  const dt = new DataTransfer();\n"
    "  const out = [];\n"
    "  for (const f of (window.__injectFiles || [])) { dt.items.add(f); out.push(f.name + ':ok(' + f.size + ')'); }\n"
    "  const getImgFile = async (u) => {\n"
    "    const img = new Image();\n"
    "    img.crossOrigin = 'anonymous';\n"
    "    await new Promise((res, rej) => { img.onload = res; img.onerror = () => rej(new Error('img')); });\n"
    "    img.src = u;\n"
    "    const c = document.createElement('canvas');\n"
    "    c.width = img.naturalWidth; c.height = img.naturalHeight;\n"
    "    c.getContext('2d').drawImage(img, 0, 0);\n"
    "    const b = c.toDataURL('image/png').split(',')[1];\n"
    "    const bin = atob(b);\n"
    "    const arr = new Uint8Array(bin.length);\n"
    "    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);\n"
    "    return new File([arr], u.split('/').pop(), { type: 'image/png' });\n"
    "  };\n"
    f"  const urls = {fig_urls_js};\n"
    "  return (async () => {\n"
    "    for (const u of urls) {\n"
    "      try { dt.items.add(await getImgFile(u)); out.push(u.split('/').pop() + ':ok'); } catch (e) { out.push(u.split('/').pop() + ':ERR ' + e.message); }\n"
    "    }\n"
    "    const input = document.querySelector('#upload-files');\n"
    "    if (!input) return 'NO_INPUT | ' + out.join(' | ');\n"
    "    input.files = dt.files;\n"
    "    input.dispatchEvent(new Event('change', { bubbles: true }));\n"
    "    return out.join(' | ');\n"
    "  })();\n"
    "})()"
)
(OUT / "finalize.js").write_text(finalize, encoding="utf-8")
print(f"finalize.js: {len(finalize)} chars")
