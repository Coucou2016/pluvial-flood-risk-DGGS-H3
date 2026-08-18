"""Paper figures from diagnostic tables (SciencePlots + matplotlib)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def require_matplotlib():
    try:
        import matplotlib.pyplot as plt  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Figures require matplotlib. Install with: pip install -e '.[plot]'"
        ) from exc


def apply_paper_style(*, chinese: bool = False) -> None:
    """
    Apply SciencePlots + Times New Roman for English paper figures.

    If ``chinese`` is True (or Chinese glyphs appear later), configure a CJK
    fallback (SimSun / Noto Sans CJK / Microsoft YaHei) after the SciencePlots
    base so Chinese labels remain readable.
    """
    require_matplotlib()
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    try:
        import scienceplots  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Figures require SciencePlots. Install with: pip install SciencePlots"
        ) from exc

    # science / no-latex keeps TNR-friendly defaults without requiring a TeX install
    plt.style.use(["science", "no-latex"])
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [
                "Times New Roman",
                "Times",
                "Nimbus Roman",
                "DejaVu Serif",
            ],
            "mathtext.fontset": "stix",
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8,
            "figure.titlesize": 11,
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    if chinese:
        _configure_cjk_fallback()


def _configure_cjk_fallback() -> None:
    """Prefer Windows/CJK fonts that can render Chinese alongside serif Latin."""
    import matplotlib as mpl
    from matplotlib import font_manager

    candidates = [
        "SimSun",
        "Noto Sans CJK SC",
        "Noto Serif CJK SC",
        "Microsoft YaHei",
        "SimHei",
        "Source Han Sans SC",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((name for name in candidates if name in available), None)
    if chosen is None:
        return
    # Keep Times New Roman first for English; append CJK for mixed labels
    serif = list(mpl.rcParams.get("font.serif", []))
    if chosen not in serif:
        serif.append(chosen)
    mpl.rcParams["font.serif"] = serif
    sans = list(mpl.rcParams.get("font.sans-serif", []))
    if chosen not in sans:
        sans.insert(0, chosen)
    mpl.rcParams["font.sans-serif"] = sans


def _needs_cjk(text: str | None) -> bool:
    if not text:
        return False
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def plot_jaccard_ladder(
    table: pd.DataFrame | Path | str,
    out_path: Path | str,
    title: str | None = None,
    caption: str | None = None,
) -> Path:
    """
    Jaccard / F1 vs coarse H3 resolution, one series per aggregation (mean/max/p90).

    Fixture or synthetic tables are pipeline QA. Do not compare the numeric Jaccard
    to Svellingen et al. 2026 (0.14 at R13 vs R10 on proprietary PFIb) unless the
    hotspot definition and labels match.
    """
    require_matplotlib()
    import matplotlib.pyplot as plt

    df = pd.read_csv(table) if not isinstance(table, pd.DataFrame) else table.copy()
    if df.empty:
        raise ValueError("Jaccard table is empty; run pluvial-diagnostics first.")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    chinese = _needs_cjk(title) or _needs_cjk(caption)
    apply_paper_style(chinese=chinese)

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6), sharex=True)
    aggs = [a for a in ("mean", "max", "p90") if a in set(df["aggregation"].astype(str))]
    style = {
        "mean": ("o", "#4C72B0"),
        "max": ("s", "#C44E52"),
        "p90": ("^", "#55A868"),
    }
    display = {"mean": "Mean", "max": "Maximum", "p90": "P90"}
    offsets = {"mean": -0.06, "max": 0.0, "p90": 0.06}
    for agg in aggs:
        sub = df.loc[df["aggregation"] == agg].sort_values("coarse_res")
        xv = sub["coarse_res"].astype(float).to_numpy() + offsets[agg]
        marker, color = style[agg]
        axes[0].plot(xv, sub["jaccard"], marker=marker, linestyle="", color=color, label=display[agg])
        axes[1].plot(xv, sub["f1"], marker=marker, linestyle="", color=color, label=display[agg])

    coarse_ticks = sorted(int(r) for r in df["coarse_res"].unique())
    axes[0].set_title("Jaccard similarity")
    axes[1].set_title("F1")
    axes[0].set_ylabel("Hotspot Jaccard")
    axes[1].set_ylabel("Hotspot F1")
    for ax in axes:
        ax.set_xlabel("Coarse H3 resolution")
        ax.set_xticks(coarse_ticks)
        ax.set_xticklabels([f"R{r}" for r in coarse_ticks])
        ax.set_ylim(0.0, 1.05)
        ax.set_xlim(coarse_ticks[0] - 0.6, coarse_ticks[-1] + 0.6)
        ax.grid(True, alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        title="Rollup",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.03),
        ncol=3,
        frameon=False,
    )

    if title:
        fig.suptitle(title, fontsize=11)

    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_spatial_cv_bars(
    fold_csv: pd.DataFrame | Path | str,
    out_path: Path | str,
    title: str | None = None,
) -> Path:
    """Per-fold spatial CV accuracy and F1 as paired markers + mean±SD error bars."""
    require_matplotlib()
    import matplotlib.pyplot as plt
    import numpy as np

    df = pd.read_csv(fold_csv) if not isinstance(fold_csv, pd.DataFrame) else fold_csv.copy()
    if df.empty:
        raise ValueError("Spatial CV fold table is empty.")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    apply_paper_style(chinese=_needs_cjk(title))

    x = np.arange(len(df))
    colors = {"accuracy": "#4C72B0", "f1": "#C44E52"}
    markers = {"accuracy": "o", "f1": "s"}
    offsets = {"accuracy": -0.08, "f1": 0.08}
    fig, ax = plt.subplots(figsize=(6.4, 3.4))

    for metric in ("accuracy", "f1"):
        ax.plot(
            x + offsets[metric],
            df[metric],
            marker=markers[metric],
            linestyle="",
            color=colors[metric],
            label=metric.capitalize(),
            markersize=5,
        )

    # Mean ± SD at a final x-position (extra half-step gap so it does not read
    # as a sixth fold), with error bars (no overlapping shaded bands).
    # ddof=0 matches the population-SD convention used in the manuscript table
    # (accuracy 0.784 ± 0.069), so the figure and table are numerically identical.
    mx = float(len(df)) + 0.5
    for metric in ("accuracy", "f1"):
        mean = float(df[metric].mean())
        sd = float(df[metric].std(ddof=0))
        ax.errorbar(
            mx + offsets[metric],
            mean,
            yerr=sd,
            fmt="D",
            color=colors[metric],
            capsize=4,
            markersize=5,
        )

    ax.set_xticks(list(range(len(df))) + [mx])
    ax.set_xticklabels([f"Fold {i}" for i in df["fold_id"].astype(int)] + ["Mean ± SD"])
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Score")
    ax.set_xlabel("H3-block spatial CV")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    if title:
        fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_workflow_schematic(
    out_path: Path | str,
    title: str | None = None,
    chinese: bool = False,
) -> Path:
    """
    Figure 1 — conceptual workflow schematic (no data dependency).

    Four stages, left to right: open multi-source inputs → H3 assembly → learning
    & blocked evaluation → diagnostics & outputs. Draws labelled boxes with
    FancyBboxPatch and arrows; Times New Roman via ``apply_paper_style``.
    """
    require_matplotlib()
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    apply_paper_style(chinese=chinese)

    stages = [
        {
            "title": "Open multi-source inputs",
            "color": "#4C72B0",
            "items": [
                "Flood labels\n(DEP stormwater, 311, USGS Ida HWM)",
                "Static predictors\n(terrain, flow-accumulation proxy, land cover,\nbuildings, hydrologic proximity)",
                "Rainfall condition r\n(constant synthetic; not radar)",
            ],
        },
        {
            "title": "H3 assembly (R9)",
            "color": "#55A868",
            "items": [
                "Join layers to H3 cells",
                "Provenance tags\n(assembly \u00b7 feature \u00b7 label \u00b7 rainfall)",
            ],
        },
        {
            "title": "Learning & blocked evaluation",
            "color": "#C44E52",
            "items": [
                "Gradient-boosting classifier\n+ continuous-risk regressor",
                "H3-block GroupKFold spatial CV\n(R7 parent blocks)",
                "Logistic, ponding & constant-class baselines",
            ],
        },
        {
            "title": "Diagnostics & outputs",
            "color": "#8172B2",
            "items": [
                "$\\mathrm{PFI}_h$(c,r)",
                "Scale-loss Jaccard ladder\n(R10 \u2192 R9 / R8)",
                "Adaptive refinement\n($\\mathrm{PFI}_h$-guided \u2192 R11)",
                "Sandy coastal-overlap diagnostic",
            ],
        },
    ]

    n = len(stages)
    fig, ax = plt.subplots(figsize=(11.2, 6.4))
    ax.set_xlim(0, n)
    ax.set_ylim(0, 1)
    ax.axis("off")

    col_w = 0.92
    gap = (1.0 - col_w) / 2.0
    x_left = 0.02

    # Title inside each column, body boxes below
    top = 0.90
    for i, st in enumerate(stages):
        cx = x_left + gap + i * 1.0 + col_w / 2.0
        # column header
        ax.text(
            cx,
            top + 0.03,
            st["title"],
            ha="center",
            va="center",
            fontsize=10.5,
            fontweight="bold",
            color=st["color"],
        )
        # body boxes stacked
        n_items = len(st["items"])
        body_top = top - 0.04
        body_bottom = 0.34
        avail = body_top - body_bottom
        box_h = avail / n_items
        for j, item in enumerate(st["items"]):
            y0 = body_top - (j + 1) * box_h
            y1 = body_top - j * box_h
            box = FancyBboxPatch(
                (cx - col_w / 2.0, y0),
                col_w,
                box_h * 0.92,
                boxstyle="round,pad=0.006,rounding_size=0.012",
                linewidth=0.9,
                edgecolor=st["color"],
                facecolor=st["color"],
                alpha=0.10,
                mutation_aspect=1.0,
            )
            ax.add_patch(box)
            ax.text(
                cx,
                (y0 + y1) / 2.0,
                item,
                ha="center",
                va="center",
                fontsize=7.4,
                color="#1a1a1a",
                linespacing=1.25,
            )

    # Arrows between columns
    for i in range(n - 1):
        x_from = x_left + gap + (i + 1) * 1.0 - gap + 0.01
        x_to = x_left + gap + (i + 1) * 1.0 - 0.01
        for yy in (0.62, 0.30):
            arr = FancyArrowPatch(
                (x_from, yy),
                (x_to, yy),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.0,
                color="#555555",
            )
            ax.add_patch(arr)

    # Sandy negative control: dashed side-channel that bypasses the learning box
    # and enters only the negative-control diagnostic in the outputs column.
    sandy = FancyBboxPatch(
        (0.06, 0.08),
        1.0,
        0.16,
        boxstyle="round,pad=0.008,rounding_size=0.014",
        linewidth=1.1,
        linestyle="--",
        edgecolor="#4C72B0",
        facecolor="#4C72B0",
        alpha=0.06,
        mutation_aspect=1.0,
    )
    ax.add_patch(sandy)
    ax.text(
        0.56,
        0.16,
        "FEMA Sandy negative control\n(never a training label)",
        ha="center",
        va="center",
        fontsize=7.4,
        color="#1a1a1a",
        linespacing=1.25,
    )
    # dashed channel from Sandy to the stage-4 negative-control check box
    ax.plot([1.06, 3.52], [0.16, 0.16], linestyle="--", linewidth=1.1, color="#4C72B0")
    sandy_arrow = FancyArrowPatch(
        (3.52, 0.16),
        (3.52, 0.34),
        arrowstyle="-|>",
        linestyle="--",
        mutation_scale=12,
        linewidth=1.1,
        color="#4C72B0",
    )
    ax.add_patch(sandy_arrow)

    if title:
        fig.suptitle(title, fontsize=12)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_adaptive_ablation(
    ablation_csv: pd.DataFrame | Path | str,
    out_path: Path | str,
    title: str | None = None,
) -> Path:
    """Bar chart of fixed / adaptive / uniform fine cell counts from ablation CSV."""
    require_matplotlib()
    import matplotlib.pyplot as plt

    df = (
        pd.read_csv(ablation_csv)
        if not isinstance(ablation_csv, pd.DataFrame)
        else ablation_csv.copy()
    )
    if df.empty:
        raise ValueError("Ablation table is empty.")

    row = df.iloc[0]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    apply_paper_style(chinese=_needs_cjk(title))

    labels = ["Fixed R9", "Adaptive R9/R11", "Uniform R11"]
    values = [
        float(row["n_fixed_coarse"]),
        float(row["n_adaptive_mixed"]),
        float(row.get("adaptive_n_uniform_fine", float("nan"))),
    ]
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    ax.bar(labels, values, color=["#4C72B0", "#55A868", "#C44E52"])
    ax.set_ylabel("Cell count")
    for i, v in enumerate(values):
        if pd.notna(v):
            ax.text(i, float(v), f"{int(v):,}", ha="center", va="bottom", fontsize=9)
    ymax = max(v for v in values if pd.notna(v))
    ax.set_ylim(0, ymax * 1.22)

    # The fixed-coarse bar is visually tiny on a linear axis; state the two
    # comparisons in a single top-band line so the efficiency message is not lost.
    fixed, adaptive, uniform = values[0], values[1], values[2]
    if pd.notna(fixed) and pd.notna(adaptive) and pd.notna(uniform) and fixed > 0:
        ax.text(
            1.0,
            ymax * 1.10,
            f"Adaptive = {adaptive / fixed:.1f}\u00d7 fixed R9\n= {adaptive / uniform * 100:.1f}% of uniform R11",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color="#1a1a1a",
            linespacing=1.3,
        )
    if title:
        fig.suptitle(title, fontsize=11)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return out_path
