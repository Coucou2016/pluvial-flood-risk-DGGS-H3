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
    styles = {"mean": "-", "max": "--", "p90": ":"}
    for agg in aggs:
        sub = df.loc[df["aggregation"] == agg].sort_values("coarse_res")
        axes[0].plot(
            sub["coarse_res"],
            sub["jaccard"],
            marker="o",
            linestyle=styles.get(agg, "-"),
            label=agg,
        )
        axes[1].plot(
            sub["coarse_res"],
            sub["f1"],
            marker="o",
            linestyle=styles.get(agg, "-"),
            label=agg,
        )

    fine = int(df["fine_res"].iloc[0]) if "fine_res" in df.columns else None
    axes[0].set_ylabel("Hotspot Jaccard")
    axes[1].set_ylabel("Hotspot F1")
    for ax in axes:
        ax.set_xlabel("Coarse H3 resolution")
        ax.set_ylim(0.0, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend(title="Rollup")
        if fine is not None:
            ax.set_title(f"Fine = R{fine}" if ax is axes[0] else "")

    if title:
        fig.suptitle(title, fontsize=11)
    elif fine is not None:
        fig.suptitle(f"Scale-loss diagnostic (fine R{fine} hotspots vs parent rollup)", fontsize=11)

    note = caption or (
        "Mean rollup smooths extrema; max/p90 retain more fine hotspots. "
        "Not a reproduction of Svellingen et al. Jaccard 0.14."
    )
    fig.text(0.5, 0.02, note, ha="center", va="bottom", fontsize=8, wrap=True)
    fig.tight_layout(rect=(0.0, 0.08, 1.0, 0.92))
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_spatial_cv_bars(
    fold_csv: pd.DataFrame | Path | str,
    out_path: Path | str,
    title: str | None = None,
) -> Path:
    """Per-fold spatial CV accuracy and F1 bars (live fold CSV only)."""
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
    width = 0.35
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.bar(x - width / 2, df["accuracy"], width, label="Accuracy")
    ax.bar(x + width / 2, df["f1"], width, label="F1")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Fold {i}" for i in df["fold_id"].astype(int)])
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Score")
    ax.set_xlabel("H3-block spatial CV fold")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.suptitle(title or "Spatial H3-block CV (Lower Manhattan smoke)", fontsize=11)
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
                "Open flood labels\n(DEP stormwater, 311, USGS Ida HWM)",
                "Static predictors\n(elevation, slope, impervious,\nbuilding density, distance-to-water)",
                "Rainfall condition r\n(synthetic constant hook; radar TBD)",
            ],
        },
        {
            "title": "H3 assembly (R9)",
            "color": "#55A868",
            "items": [
                "Join layers to H3 cells",
                "Provenance tags:\nassembly_mode · feature_source\nlabel_source · rainfall_source",
            ],
        },
        {
            "title": "Learning & blocked evaluation",
            "color": "#C44E52",
            "items": [
                "Gradient-boosting classifier\n+ continuous risk regressor",
                "H3-block GroupKFold spatial CV\n(primary blocked evaluation)",
                "Constant-class baselines\n(always-positive & always-negative)",
                "Baselines: logistic / ponding rule",
            ],
        },
        {
            "title": "Diagnostics & outputs",
            "color": "#8172B2",
            "items": [
                "PFI_h(c,r) — rainfall-conditioned\ncell probability/index (not PFIb;\ndefinition/interface, scenario response flat)",
                "Scale-loss Jaccard ladder\n(R10 → R9 / R8)",
                "Adaptive refinement\n(PFI_h screens parents → R11)",
                "Sandy negative-control check",
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
        "Negative control\n(FEMA Sandy — never a label)",
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

    fig.suptitle(
        title
        or "Open-label H3 pluvial flood learning protocol (workflow)",
        fontsize=12,
    )
    fig.text(
        0.5,
        0.005,
        "PFI_h(c,r) is a model output, not feature importance and not PFIb. "
        "Manhattan open-data pilots; not citywide.",
        ha="center",
        va="bottom",
        fontsize=7.5,
        color="#555555",
    )
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

    labels = ["Fixed coarse", "Adaptive mixed", "Uniform fine"]
    values = [
        float(row["n_fixed_coarse"]),
        float(row["n_adaptive_mixed"]),
        float(row.get("adaptive_n_uniform_fine", float("nan"))),
    ]
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.bar(labels, values, color=["#4C72B0", "#55A868", "#C44E52"])
    ax.set_ylabel("Cell count")
    ratio = row.get("adaptive_cell_count_ratio", None)
    note = f"score_col={row.get('score_col', 'PFI_h')}"
    if ratio is not None and pd.notna(ratio):
        note += f"; adaptive/uniform={float(ratio):.3f}"
    ax.set_title(note, fontsize=9)
    fig.suptitle(title or "Adaptive vs fixed / uniform fine H3", fontsize=11)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return out_path
