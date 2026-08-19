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
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 9,
            "figure.titlesize": 12,
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

    fig, axes = plt.subplots(1, 2, figsize=(7.48, 2.93), sharex=True)  # 190 mm double-column width
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
    fig, ax = plt.subplots(figsize=(5.51, 2.93))  # 140 mm 1.5-column width

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
            "title": "Multi-source inputs",
            "color": "#4C72B0",
            "items": [
                "Flood labels\n(DEP stormwater, 311,\nUSGS Ida HWM)",
                "Static predictors\n(terrain, flow-acc.\nproxy, land cover,\nhydro. distance)",
                "Rainfall condition r\n(constant synthetic;\nnot radar)",
            ],
        },
        {
            "title": "H3 assembly (R9)",
            "color": "#55A868",
            "items": [
                "Join layers to H3 cells",
                "Provenance tags\n(assembly · feature ·\nlabel · rainfall)",
            ],
        },
        {
            "title": "Learning &\nvalidation",
            "color": "#C44E52",
            "items": [
                "Gradient-boosting\nclassifier + continuous-\nrisk regressor",
                "H3-block GroupKFold\nspatial CV\n(R7 parent blocks)",
                "Logistic, ponding &\nconstant-class\nbaselines",
            ],
        },
        {
            "title": "Diagnostics &\noutputs",
            "color": "#8172B2",
            "items": [
                "$\\mathrm{PFI}_h$(c,r)",
                "Scale-loss Jaccard\nladder (R10 → R9 / R8)",
                "Adaptive refinement\n($\\mathrm{PFI}_h$-guided → R11)",
                "Sandy coastal-overlap\ndiagnostic",
            ],
        },
    ]

    n = len(stages)
    fig, ax = plt.subplots(figsize=(7.48, 4.27))  # 190 mm double-column width
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
            fontsize=11,
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
                fontsize=8.0,
                color="#1a1a1a",
                linespacing=1.25,
            )

    # Arrows between columns
    for i in range(n - 1):
        x_from = x_left + gap + (i + 1) * 1.0 - gap + 0.01
        x_to = x_left + gap + (i + 1) * 1.0 - 0.01
        for yy in (0.62,):
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
        fontsize=8.0,
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


# --------------------------------------------------------------------------- #
# Spatial results map and resolution-effect diagnostics (reference-paper style)
# --------------------------------------------------------------------------- #


def _h3_polygon_xy(cell: str) -> list[tuple[float, float]]:
    """H3 cell boundary as [(x=lng, y=lat), ...] for matplotlib Polygon patches."""
    import h3

    boundary = h3.cell_to_boundary(cell)
    return [(lng, lat) for lat, lng in boundary]


def _load_hydro_features(hydro_path: Path | str) -> list[tuple[list[tuple[float, float]], bool]]:
    """Read NHDPlus hydro features as [(line_xy, is_polygon), ...]; empty if missing."""
    import json

    path = Path(hydro_path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        geojson = json.load(fh)
    out = []
    for feat in geojson.get("features", []):
        geom = feat.get("geometry") or {}
        if geom.get("type") in ("LineString", "MultiLineString"):
            coords = geom["coordinates"]
            if geom["type"] == "MultiLineString":
                coords = [c for part in coords for c in part]
            pts = [(x, y) for x, y in coords]
            out.append((pts, False))
        elif geom.get("type") in ("Polygon", "MultiPolygon"):
            rings = geom["coordinates"]
            if geom["type"] == "MultiPolygon":
                rings = [ring for poly in rings for ring in poly]
            out.append(([(x, y) for x, y in rings[0]], True))
    return out


def _draw_dem_background(ax, dem_path: Path | str, extent: tuple[float, float, float, float] | None = None) -> None:
    """Low-contrast grayscale DEM relief behind the hexagons; no-op if raster missing."""
    import numpy as np
    import rasterio

    path = Path(dem_path)
    if not path.exists():
        return
    try:
        with rasterio.open(path) as src:
            band = src.read(1)
            bounds = src.bounds
            nodata = src.nodata
    except Exception:
        return
    if nodata is not None:
        band = np.where(band == nodata, np.nan, band)
    band = band.astype(float)
    lo, hi = np.nanpercentile(band, 2), np.nanpercentile(band, 98)
    if hi > lo:
        band = np.clip((band - lo) / (hi - lo), 0.0, 1.0)
    ax.imshow(
        band,
        extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
        cmap="Greys",
        alpha=0.35,
        interpolation="nearest",
        zorder=0,
    )
    if extent is not None:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])


def _draw_hydro_context(ax, hydro_path: Path | str) -> None:
    """NHDPlus shoreline/flowline context: polygons as light blue fills, lines as strokes."""
    import matplotlib as mpl
    from matplotlib.patches import Polygon as MplPolygon

    features = _load_hydro_features(hydro_path)
    for pts, is_polygon in features:
        if is_polygon:
            ax.add_patch(
                MplPolygon(
                    pts,
                    closed=True,
                    facecolor="#A6CEE3",
                    edgecolor="#74A9CF",
                    linewidth=0.4,
                    alpha=0.55,
                    zorder=1,
                )
            )
        else:
            ax.plot(
                [p[0] for p in pts],
                [p[1] for p in pts],
                color="#74A9CF",
                linewidth=0.8,
                alpha=0.8,
                zorder=1,
            )


def _plot_cell_map(ax, cells: list[str], values, extent, vmin, vmax, cmap, label) -> None:
    """Colour H3 hexagon patches by ``values`` on ``ax`` with a matching colorbar."""
    import numpy as np
    from matplotlib import pyplot as plt
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.colors import Normalize

    polys = []
    for cell in cells:
        pts = _h3_polygon_xy(cell)
        if pts:
            polys.append(MplPolygon(pts, closed=True))
    vals = np.asarray(values, dtype=float)
    coll = PatchCollection(polys, cmap=cmap, norm=Normalize(vmin=vmin, vmax=vmax), edgecolor="#3a3a3a", linewidth=0.35, zorder=3)
    coll.set_array(vals)
    ax.add_collection(coll)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect(1.0 / np.cos(np.deg2rad(extent[2]) if extent[2] else 1.0))
    ax.tick_params(labelsize=9)
    cb = None
    if label is not None:
        cb = plt.colorbar(coll, ax=ax, fraction=0.046, pad=0.04, aspect=24)
        cb.set_label(label, fontsize=9)
        cb.ax.tick_params(labelsize=8)
    return cb


def plot_spatial_maps(
    observed_path: pd.DataFrame | Path | str,
    oof_path: pd.DataFrame | Path | str,
    pfi_path: pd.DataFrame | Path | str,
    dem_path: Path | str,
    hydro_path: Path | str,
    out_path: Path | str,
    title: str | None = None,
    caption: str | None = None,
) -> Path:
    """
    Three-panel H3 hexagon maps for the Lower Manhattan pilot (Figure, results).

    Panels show (a) the observed open-label flood-risk score, (b) the pooled
    out-of-fold gradient-boosting probability, and (c) the full-fit
    rainfall-conditioned index PFI_h(c, r). The DEM relief and NHDPlus
    shoreline context are drawn underneath the hexagons. Only cells for which
    all three quantities exist are drawn, so the three panels share one support.
    """
    require_matplotlib()
    import matplotlib.pyplot as plt
    import pandas as pd

    if isinstance(observed_path, pd.DataFrame):
        obs = observed_path.copy()
    else:
        obs = pd.read_parquet(observed_path)
    if isinstance(oof_path, pd.DataFrame):
        oof = oof_path.copy()
    else:
        oof = pd.read_csv(oof_path)
    if isinstance(pfi_path, pd.DataFrame):
        pfi = pfi_path.copy()
    else:
        pfi = pd.read_parquet(pfi_path)

    obs = obs[["h3_index", "flood_risk"]].rename(columns={"flood_risk": "observed"})
    oof = oof[["h3_index", "y_proba"]].rename(columns={"y_proba": "oof_prob"})
    if "scenario" in pfi.columns:
        pfi = pfi[pfi["scenario"] == "ida_like"]
    pfi = pfi[["h3_index", "PFI_h"]].rename(columns={"PFI_h": "pfi"})

    df = obs.merge(oof, on="h3_index").merge(pfi, on="h3_index")
    df = df.dropna(subset=["observed", "oof_prob", "pfi"])
    if df.empty:
        raise ValueError("No cells have all three of observed/OOF/PFI_h; check input paths.")

    df = df.sort_values("h3_index")
    cells = df["h3_index"].tolist()
    lon_min, lon_max = df["h3_index"].map(lambda c: min(p[0] for p in _h3_polygon_xy(c))).min(), df[
        "h3_index"
    ].map(lambda c: max(p[0] for p in _h3_polygon_xy(c))).max()
    lat_min, lat_max = df["h3_index"].map(lambda c: min(p[1] for p in _h3_polygon_xy(c))).min(), df[
        "h3_index"
    ].map(lambda c: max(p[1] for p in _h3_polygon_xy(c))).max()
    extent = (lon_min - 0.004, lon_max + 0.004, lat_min - 0.004, lat_max + 0.004)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    chinese = _needs_cjk(title) or _needs_cjk(caption)
    apply_paper_style(chinese=chinese)

    fig, axes = plt.subplots(1, 3, figsize=(7.48, 2.74))  # 190 mm double-column width
    panels = [
        ("observed", "Observed open-label risk", "Open-label risk (0\u20131)"),
        ("oof_prob", "Out-of-fold model probability", "Model probability"),
        ("pfi", r"Full-fit $\mathrm{PFI}_h(c,r)$", r"$\mathrm{PFI}_h$"),
    ]
    cmap = "viridis"
    for ax, (col, ptitle, clabel) in zip(axes, panels):
        _draw_dem_background(ax, dem_path, extent)
        _draw_hydro_context(ax, hydro_path)
        _plot_cell_map(ax, cells, df[col], extent, 0.0, 1.0, cmap, clabel)
        ax.set_title(ptitle, fontsize=11)
        ax.set_xlabel("Longitude (\u00b0)", fontsize=10)
        ax.set_ylabel("Latitude (\u00b0)", fontsize=10)
    for ax, tag in zip(axes, "abc"):
        ax.text(
            0.02,
            0.97,
            f"({tag})",
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            ha="left",
            va="top",
            zorder=10,
        )
    for ax in axes[1:]:
        ax.set_ylabel("")

    if title:
        fig.suptitle(title, fontsize=12)
    fig.tight_layout(w_pad=1.2)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return out_path


def _resolution_rollups(r10_scores: pd.Series, out_res: int) -> pd.Series:
    """Mean aggregation of R10 open-label scores onto ``out_res`` parent cells."""
    import h3

    parents = r10_scores.index.map(lambda c: h3.cell_to_parent(c, out_res))
    tmp = pd.DataFrame({"parent": parents, "score": r10_scores.values})
    return tmp.groupby("parent")["score"].mean()


def _hotspot_cells(scores: pd.Series, quantile: float = 0.9) -> set[str]:
    """Cells at or above the ``quantile`` of their resolution's own scores."""
    thr = scores.quantile(quantile)
    return set(scores[scores >= thr].index)


def _pairwise_hotspot_jaccard(fine_scores: pd.Series, coarse_scores: pd.Series) -> float:
    """Jaccard between fine hotspots projected to coarse parents and coarse hotspots."""
    import h3

    fine_hot = _hotspot_cells(fine_scores)
    coarse_res = h3.get_resolution(next(iter(coarse_scores.index)))
    fine_parents = {h3.cell_to_parent(c, coarse_res) for c in fine_hot}
    coarse_hot = _hotspot_cells(coarse_scores)
    inter = len(fine_parents & coarse_hot)
    union = len(fine_parents | coarse_hot)
    return inter / union if union else float("nan")


def plot_resolution_effects(
    r10_labels_path: pd.DataFrame | Path | str,
    out_path: Path | str,
    quantile: float = 0.9,
    title: str | None = None,
    caption: str | None = None,
) -> Path:
    """
    Resolution-effect diagnostics (reference-paper style, one two-panel figure).

    (a) Violin plots of the open-label score at R10, R9, and R8 (mean rollup),
    showing the variance compression as the grid coarsens. (b) Jaccard
    similarity between hotspot sets (top ``quantile``) at R10, R9, and R8,
    computed on the coarser support in each pair so the R10-vs-R9 and
    R10-vs-R8 entries reproduce the scale-loss ladder exactly.
    """
    require_matplotlib()
    import h3
    import matplotlib.pyplot as plt
    import numpy as np

    if isinstance(r10_labels_path, pd.DataFrame):
        df = r10_labels_path[["h3_index", "flood_risk"]].copy()
    else:
        df = pd.read_parquet(r10_labels_path)[["h3_index", "flood_risk"]].copy()
    if df.empty:
        raise ValueError("R10 label table is empty.")
    s10 = df.set_index("h3_index")["flood_risk"]
    s9 = _resolution_rollups(s10, 9)
    s8 = _resolution_rollups(s10, 8)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    chinese = _needs_cjk(title) or _needs_cjk(caption)
    apply_paper_style(chinese=chinese)

    fig, (ax_v, ax_h) = plt.subplots(1, 2, figsize=(7.48, 2.96))  # 190 mm double-column width

    # --- panel (a): score distribution across resolutions ---
    data = [s10.values, s9.values, s8.values]
    vp = ax_v.violinplot(data, positions=[0, 1, 2], showmeans=True, showextrema=True, widths=0.7)
    for i, body in enumerate(vp["bodies"]):
        body.set_facecolor(["#4C72B0", "#55A868", "#DD8452"][i])
        body.set_alpha(0.6)
    rng = np.random.default_rng(20260819)
    for i, (vals, color) in enumerate(zip(data, ["#4C72B0", "#55A868", "#DD8452"])):
        jitter = rng.uniform(-0.22, 0.22, size=len(vals))
        ax_v.scatter(i + jitter, vals, s=9, color=color, alpha=0.35, linewidths=0, zorder=5)
    ax_v.set_xticks([0, 1, 2])
    ax_v.set_xticklabels([f"R10 (n={len(s10)})", f"R9 (n={len(s9)})", f"R8 (n={len(s8)})"])
    ax_v.set_ylabel("Open-label score")
    ax_v.set_ylim(0.0, 1.05)
    ax_v.grid(True, axis="y", alpha=0.3)
    ax_v.set_title("Score distribution by resolution (mean rollup)")
    ax_v.text(0.02, 0.97, "(a)", transform=ax_v.transAxes, fontsize=12, fontweight="bold", ha="left", va="top")

    # --- panel (b): Jaccard cross-resolution similarity matrix ---
    j10_9 = _pairwise_hotspot_jaccard(s10, s9)
    j10_8 = _pairwise_hotspot_jaccard(s10, s8)
    j9_8 = _pairwise_hotspot_jaccard(s9, s8)
    matrix = np.array(
        [
            [1.0, j9_8, j10_8],
            [j9_8, 1.0, j10_9],
            [j10_8, j10_9, 1.0],
        ]
    )
    labels = ["R8", "R9", "R10"]
    im = ax_h.imshow(matrix, cmap="YlGnBu", vmin=0.0, vmax=1.0)
    ax_h.set_xticks(range(3))
    ax_h.set_yticks(range(3))
    ax_h.set_xticklabels(labels)
    ax_h.set_yticklabels(labels)
    ax_h.set_xlabel("Hotspot resolution")
    ax_h.set_ylabel("Hotspot resolution")
    for i in range(3):
        for j in range(3):
            val = matrix[i, j]
            color = "white" if val >= 0.6 else "black"
            ax_h.text(j, i, f"{val:.3f}", ha="center", va="center", fontsize=9, color=color)
    ax_h.grid(which="major", color="white", linewidth=1.2, alpha=0.7)
    ax_h.set_xticks(np.arange(3))
    ax_h.set_yticks(np.arange(3))
    ax_h.set_title("Cross-resolution hotspot Jaccard similarity (q = 0.9)")
    ax_h.text(0.02, 0.97, "(b)", transform=ax_h.transAxes, fontsize=12, fontweight="bold", ha="left", va="top", color="white")
    fig.colorbar(im, ax=ax_h, fraction=0.046, pad=0.04, label="Jaccard similarity")

    if title:
        fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    fig.savefig(out_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_multi_resolution_spatial(
    r10_labels_path: pd.DataFrame | Path | str,
    dem_path: Path | str,
    hydro_path: Path | str,
    out_path: Path | str,
    title: str | None = None,
    caption: str | None = None,
) -> Path:
    """Figure 4 — multi-resolution open-label score surface (R10 / R9 / R8).

    Three panels on the same label-assembly footprint: (a) R10 open-label
    flood-risk score (n = 991), (b) mean rollup to R9 (n = 160), and (c) mean
    rollup to R8 (n = 31). All panels share one 0-1 viridis colour scale so the
    smoothing that accompanies coarsening is visible directly. The aggregation
    is the same mean rollup used by the resolution-effect diagnostics; no new
    statistics are introduced here.
    """
    require_matplotlib()
    import matplotlib.pyplot as plt
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize

    if isinstance(r10_labels_path, pd.DataFrame):
        df = r10_labels_path[["h3_index", "flood_risk"]].copy()
    else:
        df = pd.read_parquet(r10_labels_path)[["h3_index", "flood_risk"]].copy()
    if df.empty:
        raise ValueError("R10 label table is empty.")
    s10 = df.set_index("h3_index")["flood_risk"]
    s9 = _resolution_rollups(s10, 9)
    s8 = _resolution_rollups(s10, 8)

    # Common geographic footprint from the finest (R10) support.
    r10_cells = list(s10.index)
    lon_min = min(min(p[0] for p in _h3_polygon_xy(c)) for c in r10_cells)
    lon_max = max(max(p[0] for p in _h3_polygon_xy(c)) for c in r10_cells)
    lat_min = min(min(p[1] for p in _h3_polygon_xy(c)) for c in r10_cells)
    lat_max = max(max(p[1] for p in _h3_polygon_xy(c)) for c in r10_cells)
    extent = (lon_min - 0.004, lon_max + 0.004, lat_min - 0.004, lat_max + 0.004)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    chinese = _needs_cjk(title) or _needs_cjk(caption)
    apply_paper_style(chinese=chinese)

    fig, axes = plt.subplots(1, 3, figsize=(7.48, 2.74))  # 190 mm double-column width
    panels = [
        (list(s10.index), s10.values, f"R10 (n = {len(s10)})"),
        (list(s9.index), s9.values, f"R9 mean rollup (n = {len(s9)})"),
        (list(s8.index), s8.values, f"R8 mean rollup (n = {len(s8)})"),
    ]
    cmap = "viridis"
    for ax, (cells, vals, ptitle) in zip(axes, panels):
        _draw_dem_background(ax, dem_path, extent)
        _draw_hydro_context(ax, hydro_path)
        _plot_cell_map(ax, cells, vals, extent, 0.0, 1.0, cmap, None)
        ax.set_title(ptitle, fontsize=11)
        ax.set_xlabel("Longitude (\u00b0)", fontsize=10)
        ax.set_ylabel("Latitude (\u00b0)", fontsize=10)
    for ax, tag in zip(axes, "abc"):
        ax.text(
            0.02,
            0.97,
            f"({tag})",
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            ha="left",
            va="top",
            zorder=10,
        )
    for ax in axes[1:]:
        ax.set_ylabel("")

    # One shared colour bar for all three panels, placed in a fixed axis to
    # avoid tight_layout / colorbar conflicts.
    sm = ScalarMappable(norm=Normalize(vmin=0.0, vmax=1.0), cmap=cmap)
    sm.set_array([])
    fig.subplots_adjust(left=0.07, right=0.87, bottom=0.16, top=0.90, wspace=0.38)
    cbar_ax = fig.add_axes([0.885, 0.22, 0.015, 0.56])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("Open-label score", fontsize=9)
    cb.ax.tick_params(labelsize=8)

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
    fig, ax = plt.subplots(figsize=(5.51, 3.12))  # 140 mm 1.5-column width
    ax.bar(labels, values, color=["#4C72B0", "#55A868", "#C44E52"])
    ax.set_ylabel("Cell count")
    for i, v in enumerate(values):
        if pd.notna(v):
            ax.text(i, float(v), f"{int(v):,}", ha="center", va="bottom", fontsize=9)
    ymax = max(v for v in values if pd.notna(v))
    ax.set_ylim(0, ymax * 1.30)

    # The fixed-coarse bar is visually tiny on a linear axis; state the two
    # comparisons in a single top-band line so the efficiency message is not lost.
    fixed, adaptive, uniform = values[0], values[1], values[2]
    if pd.notna(fixed) and pd.notna(adaptive) and pd.notna(uniform) and fixed > 0:
        ax.text(
            1.0,
            ymax * 1.02,
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
