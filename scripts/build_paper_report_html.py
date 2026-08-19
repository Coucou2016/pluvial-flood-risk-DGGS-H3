"""Build self-contained paper/report HTML with Base64-embedded figures.

Primary narrative source: docs/paper/report.md (deep teacher-like prose).
Figures are injected as data:image/png;base64 — no CDN.
"""

from __future__ import annotations

import base64
import csv
import html as htmllib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "paper"
FIG = PAPER / "figures"


def b64_png(path: Path) -> str | None:
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("ascii")


def figure_block(key: str, data: str | None, alt: str, caption_html: str) -> str:
    if not data:
        return f"<p><em>Figure missing: {htmllib.escape(alt)}</em></p>"
    return (
        f'<figure id="fig-{key}">'
        f'<img src="data:image/png;base64,{data}" alt="{htmllib.escape(alt)}" '
        f'style="max-width:100%;height:auto;border:1px solid #ccc;"/>'
        f"<figcaption>{caption_html}</figcaption></figure>"
    )


def md_to_simple_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    in_table = False
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def close_table() -> None:
        nonlocal in_table
        if in_table:
            out.append("</table>")
            in_table = False

    def inline_fmt(text: str) -> str:
        esc = htmllib.escape(text)
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        esc = re.sub(r"`([^`]+)`", r"<code>\1</code>", esc)
        esc = re.sub(
            r"\[([^\]]+)\]\((https?://[^)]+)\)",
            r'<a href="\2">\1</a>',
            esc,
        )
        return esc

    for line in lines:
        if line.startswith("# "):
            close_lists()
            close_table()
            out.append(f"<h1>{inline_fmt(line[2:])}</h1>")
            continue
        if line.startswith("## "):
            close_lists()
            close_table()
            title = line[3:]
            # Stable anchors for TOC
            slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title).strip("-").lower()
            out.append(f'<h2 id="{htmllib.escape(slug)}">{inline_fmt(title)}</h2>')
            continue
        if line.startswith("### "):
            close_lists()
            close_table()
            out.append(f"<h3>{inline_fmt(line[4:])}</h3>")
            continue
        if line.startswith("#### "):
            close_lists()
            close_table()
            out.append(f"<h4>{inline_fmt(line[5:])}</h4>")
            continue
        if line.startswith("|") and "|" in line[1:]:
            close_lists()
            if re.match(r"^\|?\s*-+", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not in_table:
                out.append("<table>")
                in_table = True
                tag = "th"
            else:
                tag = "td"
            row = "".join(f"<{tag}>{inline_fmt(c)}</{tag}>" for c in cells)
            out.append(f"<tr>{row}</tr>")
            continue
        if in_table:
            close_table()
        if line.strip() == "---":
            close_lists()
            out.append("<hr/>")
            continue
        if line.strip() == "":
            close_lists()
            continue
        # unordered list
        m_ul = re.match(r"^[-*] (.+)$", line)
        if m_ul:
            close_table()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline_fmt(m_ul.group(1))}</li>")
            continue
        # ordered list
        m_ol = re.match(r"^(\d+)\. (.+)$", line)
        if m_ol:
            close_table()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline_fmt(m_ol.group(2))}</li>")
            continue
        close_lists()
        # block math-ish lines
        if line.strip().startswith("\\[") or line.strip().endswith("\\]"):
            out.append(f"<pre class='eq'>{htmllib.escape(line)}</pre>")
            continue
        if line.strip().startswith(">"):
            out.append(f"<blockquote>{inline_fmt(line.lstrip('> ').strip())}</blockquote>")
            continue
        out.append(f"<p>{inline_fmt(line)}</p>")
    close_lists()
    close_table()
    return "\n".join(out)


def inject_figures(body_html: str, figs: dict[str, str | None]) -> str:
    """Replace markdown figure path mentions with Base64 <figure> blocks."""
    replacements = [
        (
            "docs/paper/figures/workflow_schematic.png",
            figure_block(
                "workflow",
                figs["workflow"],
                "Workflow schematic",
                "<strong>图 1 · Figure 1</strong> — 开放标签 H3 雨洪学习协议的概念工作流（SciencePlots + Times New Roman）。"
                "<br/><em>如何读：</em>从左到右四列——(1) 开放多源输入；(2) H3 组装（R9 + provenance 标签）；(3) 学习与分块评价（GBM + H3 块 GroupKFold 空间 CV + 常量类基线恒判正/恒判负）；(4) 诊断与输出（PFI_h(c,r)、Jaccard 阶梯、自适应加密、Sandy 海岸淹没重叠诊断，其中 Sandy 为虚线旁路、绕过学习框、只进入 Sandy 诊断框）。"
                "<br/><em>意义：</em>一张图讲清整条协议与「证据—边界」纪律，对应手稿 Methods。"
                "<br/><em>结论：</em>PFI_h(c,r) 是模型输出，不是特征重要性，也不是 PFIb；当前情景响应平坦；证据仅限 Manhattan 开放数据试点，非全市。",
            ),
        ),
        (
            "docs/paper/figures/spatial_maps.png",
            figure_block(
                "spatial_maps",
                figs["spatial_maps"],
                "Spatial results maps",
                "<strong>图 2 · Figure 2</strong> — 空间结果图：Lower Manhattan 试点（n=141 个 R9 六边形）三面板同支撑（SciencePlots + TNR）。"
                "<br/><em>如何读：</em>(a) 观测开放标签分（二元化：无证据=0，任一证据=高值）；(b) H3 块空间 CV 留出概率；(c) 部署指数 PFI_h(c,r)（ida_like r=75 mm/h；全情景不变，见 §5.6）。同色标 0–1，灰色底图为 DEM 地形，浅蓝为 NHDPlus 岸线水系。"
                "<br/><em>意义：</em>对照参考论文「先空间图后统计图」体例；三面板同源同支撑，观测~留出 r=0.245、观测~PFI_h r=0.468、留出~PFI_h r=0.509，与「排序判别中等」叙事一致。"
                "<br/><em>结论：</em>仅视觉检视，非独立验证；不得把图面高低当作额外证据。",
            ),
        ),
        (
            "docs/paper/figures/spatial_cv_folds.png",
            figure_block(
                "spatial",
                figs["spatial"],
                "Spatial CV fold markers",
                "<strong>图 3 · Figure 3</strong> — 空间 H3 块 CV 各折 Accuracy 与 F1（SciencePlots + Times New Roman）。"
                "<br/><em>如何读：</em>横轴为折号 + Mean±SD，纵轴为 0–1 分数；成对标记点表示同一折的 Accuracy/F1，末位为 Mean±SD 误差棒。"
                "<br/><em>意义：</em>展示评价协议的折间稳定性，而非单一乐观分数。"
                "<br/><em>结论：</em>多数折 Accuracy≈0.71–0.77，Fold4 更高；与表 1 均值一致。样本仍是 Lower Manhattan smoke。",
            ),
        ),
        (
            "docs/paper/figures/jaccard_by_resolution.png",
            figure_block(
                "jaccard",
                figs["jaccard"],
                "Jaccard ladder",
                "<strong>图 4 · Figure 4</strong> — 开放标签热点 Jaccard/F1 随粗分辨率变化（SciencePlots + TNR）。"
                "<br/><em>如何读：</em>左 Jaccard similarity、右 F1；标记形状/颜色区分 mean/max/p90 上卷（共享图例）。"
                "<br/><em>意义：</em>量化 MAUP/尺度损失：决策尺度变粗时，热点集合可能面目全非。"
                "<br/><em>结论：</em>mean@R8 损失最大；不得与 PFIb 文献的 0.14 直接等同。",
            ),
        ),
        (
            "docs/paper/figures/resolution_effects.png",
            figure_block(
                "resolution",
                figs["resolution"],
                "Resolution effects",
                "<strong>图 5 · Figure 5</strong> — 分辨率效应：(a) 开放标签分在 R10/R9/R8 的分布压缩；(b) Jaccard 热点持久性矩阵（SciencePlots + TNR）。"
                "<br/><em>如何读：</em>(a) 三条小提琴由宽双峰压缩为窄带；(b) 非对角项远离对角线衰减：J(R10,R9)=0.977、J(R10,R8)=0.167、J(R9,R8)=0.167。"
                "<br/><em>意义：</em>把尺度损失从阶梯表扩展为「分布压缩 + 集合持久性」两种互补统计视图，对齐参考论文 Fig 5 类型。"
                "<br/><em>结论：</em>数值与表 3/图 4 完全一致；粗化同时压缩分布并瓦解热点持久性。",
            ),
        ),
        (
            "docs/paper/figures/adaptive_ablation.png",
            figure_block(
                "adaptive",
                figs["adaptive"],
                "Adaptive ablation",
                "<strong>图 6 · Figure 6</strong> — 固定 R9 / 自适应 R9/R11 / 均匀 R11 单元数。"
                "<br/><em>如何读：</em>三柱分别为 Fixed R9、Adaptive R9/R11、Uniform R11；顶部标注「27.9× fixed R9 = 56.9% of uniform R11」。"
                "<br/><em>意义：</em>展示自适应在计算预算与局部细化之间的折中。"
                "<br/><em>结论：</em>自适应 = 27.9× 固定 R9 = 56.9% 均匀 R11；非全市成本声明。",
            ),
        ),
    ]
    for path_token, block in replacements:
        # Replace the heading+path paragraph pattern produced from markdown
        # e.g. <h4>图 1 · `docs/paper/figures/spatial_cv_folds.png`</h4>
        pattern = re.compile(
            rf"<h4>[^<]*<code>{re.escape(path_token)}</code></h4>",
            re.IGNORECASE,
        )
        body_html, n = pattern.subn(block, body_html, count=1)
        if n == 0:
            # Fallback: insert after first mention of the path in any paragraph
            needle = f"<code>{htmllib.escape(path_token)}</code>"
            if needle in body_html:
                body_html = body_html.replace(needle, needle + "</p>" + block + "<p>", 1)
            else:
                body_html += block
    return body_html


def main() -> None:
    figs = {
        "workflow": b64_png(FIG / "workflow_schematic.png"),
        "spatial_maps": b64_png(FIG / "spatial_maps.png"),
        "spatial": b64_png(FIG / "spatial_cv_folds.png"),
        "jaccard": b64_png(FIG / "jaccard_by_resolution.png"),
        "resolution": b64_png(FIG / "resolution_effects.png"),
        "adaptive": b64_png(FIG / "adaptive_ablation.png"),
    }
    meta = json.loads((ROOT / "models" / "nyc_smoke" / "run_metadata.json").read_text(encoding="utf-8"))
    md = (PAPER / "report.md").read_text(encoding="utf-8")
    body = md_to_simple_html(md)
    body = inject_figures(body, figs)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    css = """
:root { --ink:#1a1a1a; --muted:#555; --line:#ddd; --bg:#fafafa; --accent:#0b3d5c; }
* { box-sizing: border-box; }
body { font-family: "Times New Roman", Times, serif; color: var(--ink); line-height:1.55; margin:0; background:#fff; }
.wrap { max-width: 920px; margin: 0 auto; padding: 28px 24px 64px; }
.banner { background: var(--bg); border: 1px solid var(--line); padding: 10px 14px; margin-bottom: 18px; font-size: 0.92rem; color: var(--muted); }
h1 { font-size: 1.55rem; color: var(--accent); margin-top: 0; }
h2 { color: var(--accent); border-bottom: 1px solid var(--line); padding-bottom: 4px; margin-top: 2rem; }
h3 { margin-top: 1.4rem; }
h4 { margin-top: 1.1rem; color: #333; }
table { border-collapse: collapse; width: 100%; margin: 12px 0 8px; font-size: 0.92rem; }
th, td { border: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: #eef3f7; }
figure { margin: 18px 0 28px; }
figcaption { font-size: 0.92rem; color: #222; margin-top: 8px; line-height: 1.45; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.88em; }
blockquote { border-left: 4px solid var(--accent); margin: 12px 0; padding: 6px 14px; background: #f3f7fb; }
pre.eq { background: #f7f7f7; padding: 10px 12px; overflow-x: auto; }
hr { border: none; border-top: 1px solid var(--line); margin: 24px 0; }
ul, ol { margin: 8px 0 12px; }
a { color: var(--accent); }
@media print { a { color: inherit; text-decoration: none; } }
"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Research Report — Open-label H3 Pluvial Flood Learning (Lower Manhattan Smoke)</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<div class="banner">
自包含报告 · Base64 内嵌图 · 内联 CSS · 无 CDN · 生成 {now} · framework {meta.get('framework_version')} ·
n_cells={meta.get('n_cells')} · 数值仅来自 outputs/ 与 models/nyc_smoke/ · 非 PFIb · LM≠citywide
</div>
{body}
</div>
</body>
</html>
"""

    out_html = PAPER / "report.html"
    out_html.write_text(html, encoding="utf-8")
    (ROOT / "report.html").write_text(html, encoding="utf-8")
    print(f"wrote {out_html} ({out_html.stat().st_size} bytes)")
    print(f"wrote {ROOT / 'report.html'} ({(ROOT / 'report.html').stat().st_size} bytes)")

    # Also refresh manuscript.html from manuscript.md
    ms = (PAPER / "manuscript.md").read_text(encoding="utf-8")
    ms_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>Manuscript — Adaptive H3 open-label pluvial learning</title>
<style>
body{{font-family:"Times New Roman",Times,serif;max-width:900px;margin:24px auto;padding:0 16px;line-height:1.5}}
table{{border-collapse:collapse;width:100%;font-size:0.92rem}}
th,td{{border:1px solid #ccc;padding:4px 6px;vertical-align:top}}th{{background:#eef3f7}}
code{{font-family:Consolas,monospace;font-size:0.9em}}
h1,h2,h3{{color:#0b3d5c}}
blockquote{{border-left:4px solid #0b3d5c;padding:6px 12px;background:#f3f7fb}}
</style></head><body>
{md_to_simple_html(ms)}
</body></html>
"""
    ms_path = PAPER / "manuscript.html"
    ms_path.write_text(ms_html, encoding="utf-8")
    print(f"wrote {ms_path} ({ms_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
