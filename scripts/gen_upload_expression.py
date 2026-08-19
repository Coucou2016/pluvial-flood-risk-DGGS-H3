"""Generate per-file Runtime.evaluate JS expressions (base64 embedded) for
injecting the three text files into the ChatGPT upload input."""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

files = {
    "manuscript.md": (ROOT / "docs/paper/manuscript.md", "text/markdown"),
    "audit.md": (ROOT / "docs/paper/audit.md", "text/markdown"),
    "figures.py": (ROOT / "src/pluvial_flood_risk/figures.py", "text/x-python"),
}

out_dir = ROOT / ".upload_chunks"
out_dir.mkdir(exist_ok=True)

for idx, (name, (path, mime)) in enumerate(files.items()):
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    expr = f"""(() => {{
  const b64 = {b64!r};
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  window.__injectFiles = window.__injectFiles || [];
  window.__injectFiles.push(new File([arr], {name!r}, {{ type: {mime!r} }}));
  return {name!r} + ':ok(' + arr.length + ')';
}})()"""
    target = out_dir / f"inject_{idx}_{name.replace('.', '_')}.js"
    target.write_text(expr, encoding="utf-8")
    print(f"wrote {target} ({len(expr)} chars) name={name}")
