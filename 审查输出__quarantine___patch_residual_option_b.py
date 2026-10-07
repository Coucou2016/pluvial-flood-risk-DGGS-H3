"""Patch report.md + residual manuscript.md to Option B (n=262) truth."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def patch_report() -> None:
    p = ROOT / "docs" / "paper" / "report.md"
    t = p.read_text(encoding="utf-8")

    repls = [
        (
            "| LM smoke（Lower Manhattan smoke） | 下曼哈顿包围盒上的开放数据烟雾测试（`n_cells=141`），**≠ citywide** |",
            "| LM Option B（Lower Manhattan） | 论文 bbox 上的开放数据试点（`n_cells=262`），**≠ citywide**；遗留 smoke 141 仅 QA |",
        ),
        (
            "| 训练主表 | R9 | `n_cells=141` |",
            "| 训练主表 | R9 | `n_cells=262`（Option B） |",
        ),
        ("| n_cells | 141 |", "| n_cells | 262 |"),
        (
            "| accuracy mean ± std | 0.781432 ± 0.123141 |",
            "| accuracy mean ± std | 0.808895 ± 0.045779 |",
        ),
        (
            "| 多数类（恒判正）基线 accuracy | **0.662** |",
            "| 多数类（恒判正）基线 accuracy | **0.629** |",
        ),
        (
            "| 多数类（恒判正）基线 F1 | **0.794** |",
            "| 多数类（恒判正）基线 F1 | **0.762** |",
        ),
        (
            "| 留出 ROC-AUC（pooled） | **0.780** |",
            "| 留出 ROC-AUC（pooled） | **0.847** |",
        ),
        (
            "| n_fixed_coarse (R9) | 141 |",
            "| n_fixed_coarse (R9) | 262 |",
        ),
        ("| n_cells | 141 |", "| n_cells | 262 |"),  # may already replaced
        (
            "| n_cells | **956** | 141 |",
            "| n_cells | **956** | 262 |",
        ),
        (
            "| spatial_cv_accuracy_mean ± std | **0.821 ± 0.033** | 0.781 ± 0.123 |",
            "| spatial_cv_accuracy_mean ± std | **0.821 ± 0.033** | 0.809 ± 0.046 |",
        ),
        (
            "| always-positive accuracy | **0.475** | 0.662 |",
            "| always-positive accuracy | **0.475** | 0.629 |",
        ),
        (
            "| always-positive F1（折内均值） | **0.643** | 0.794 |",
            "| always-positive F1（折内均值） | **0.643** | 0.762 |",
        ),
        (
            "| 恒定多数类（真多数类） | 恒判负，acc 0.525 | 恒判正，acc 0.662 |",
            "| 恒定多数类（真多数类） | 恒判负，acc 0.525 | 恒判正，acc 0.629 |",
        ),
        (
            "| 模型是否超过恒定多数类 accuracy | **是（0.821 > 0.525）** | 是（0.781 > 0.662） |",
            "| 模型是否超过恒定多数类 accuracy | **是（0.821 > 0.525）** | 是（0.809 > 0.629） |",
        ),
        (
            "| 模型是否超过 always-positive F1 | **是（0.819 > 0.643）** | 是（0.822 > 0.794） |",
            "| 模型是否超过 always-positive F1 | **是（0.819 > 0.643）** | 是（0.846 > 0.762） |",
        ),
        (
            "| ROC-AUC（pooled，留出） | **0.883** | 0.780 |",
            "| ROC-AUC（pooled，留出） | **0.883** | 0.847 |",
        ),
        (
            "| LM smoke n=141 ≠ citywide | 锁定 |",
            "| LM Option B n=262 ≠ citywide | 锁定 |",
        ),
    ]
    for a, b in repls:
        if a in t:
            t = t.replace(a, b)
            print("report OK:", a[:60])
        else:
            print("report MISS:", a[:60])

    # Executive summary paragraph (replace whole block starting at key phrase)
    old_exec = (
        "在 H3 分辨率 R9 上组装 **n_cells = 141** 个六边形单元，`assembly_mode=opendata`。"
        "主（**分块评价**）指标为 **spatial H3-block CV（空间 H3 块交叉验证）**：准确率均值 "
        "**0.781432 ± 0.123141**，F1 均值 **0.821905 ± 0.116**（来源：`models/nyc_smoke/run_metadata.json`，"
        "`created_utc=2026-08-24T14:52:10Z`）。**关键修订（2026-08-23 C1 → 2026-08-24 M4）：** "
        "留出样本正类占比 **67.4%**（剔除 DEP category 3 海岸高潮位后，并将 DEP 主层从 2050 海平面上升改回**当前海平面** "
        '"Moderate Flood with Current Sea Levels" 层），恒判正的多数类平凡基线在同样折上可达 accuracy **0.662**、'
        "F1 **0.794**，此时模型 **0.781 / 0.822 已超过**该平凡基线（来源：`outputs/classification_baselines.json`）。"
        "尺度损失用开放证据 **Jaccard ladder** 诊断（exact top-10% 预算、H3 index tie-break）：细 R10→粗 R9 **mean** "
        "聚合 Jaccard = **0.180**、细 R10→粗 R8 **mean** 聚合 Jaccard = **0.111**（R10 为原生 overlay，无 parent "
        "inheritance；不得写成“复现了 Svellingen 的 0.14”）。自适应相对均匀细网格（R11）单元数比 "
        "**adaptive_cell_count_ratio ≈ 0.701**。"
    )
    new_exec = (
        "在 H3 分辨率 R9 上组装 **n_cells = 262** 个六边形单元（Major Revision **Option B**：论文 Lower Manhattan "
        "bbox `[-74.02, 40.70, -73.97, 40.76]`；遗留 smoke 141 仅 QA），`assembly_mode=opendata`。"
        "主（**分块评价**）指标为 **spatial H3-block CV**：准确率均值 **0.809 ± 0.046**，F1 均值 **0.846**"
        "（来源：`models/nyc_smoke/run_metadata.json` / `outputs/paper_results.json`，"
        "`created_utc=2026-08-30T17:00:44Z`）。留出正类占比 **63.0%**，恒判正基线 accuracy **0.629**、F1 **0.762**，"
        "模型 **0.809 / 0.846 超过**该基线（`outputs/classification_baselines.json`）。留出 pooled ROC-AUC "
        "**0.847**、AP **0.851**。尺度损失用开放证据 **Jaccard ladder**（tie-aware fractional membership + "
        "projected-parent-area budgets）：细 R10→粗 R9 **mean** Jaccard = **0.216**、R10→R8 **mean** "
        "Jaccard = **0.105**（不得写成“复现了 Svellingen 的 0.14”）。自适应相对均匀细网格（R11）单元数比 "
        "**adaptive_cell_count_ratio ≈ 0.563**。图 2(c) 与自适应仅使用 **deployment_full** 全量重拟合模型。"
        "\n\n> **历史注记（pre-Option-B，n=141 smoke）：** 修订前主表曾误用较小 smoke bbox（n=141，正类≈67.4%，"
        "acc≈0.781 / F1≈0.822 / ROC-AUC≈0.780）。该数字**不是**当前 Option B 真相，仅作审计轨迹。"
    )
    if old_exec in t:
        t = t.replace(old_exec, new_exec)
        print("report OK: exec summary")
    else:
        print("report MISS: exec summary — trying softer replace")
        # Soft: replace first occurrence of key n_cells line pattern
        t2 = t.replace("**n_cells = 141**", "**n_cells = 262**（Option B）", 1)
        if t2 != t:
            t = t2
            print("report soft: n_cells line")

    # Study area wording
    t = t.replace(
        "这是 **pilot smoke extent**，**不是**纽约全市。",
        "这是 **Lower Manhattan Option B 试点范围**（n=262；遗留 smoke 141 仅 QA），**不是**纽约全市。",
    )

    # §5.1 narrative block — replace key sentence clusters with replace_all where safe
    cluster = [
        (
            "先看正类占比（0.674，即 67.4% 留出单元为正），再看多数类基线（恒判正 acc 0.662 / F1 0.794），最后才看模型分数（0.781 / 0.822）。模型分数**超过**多数类基线（0.781 > 0.662；0.822 > 0.794），说明在空间块留出下模型具备超过“闭眼判洪”的判别力；留出 ROC-AUC 0.780、AP 0.805 高于 0.674 随机基线，进一步支持**中等排序判别力**。但 R² 仍接近 0（0.048），说明证据分回归对“人造 evidence score”的解释力有限。随机划分准确率（0.759）低于空间 CV，仅提示“换协议分数会变”，不能当主结果。",
            "先看正类占比（0.630，即 63.0% 留出单元为正），再看多数类基线（恒判正 acc 0.629 / F1 0.762），最后才看模型分数（0.809 / 0.846）。模型分数**超过**多数类基线（0.809 > 0.629；0.846 > 0.762）；留出 ROC-AUC 0.847、AP 0.851 高于 0.630 随机基线，支持**中等偏强排序判别力**。证据分 R² 为 0.227 ± 0.196，解释力有限。随机划分准确率（0.792）仅作诊断，不能当主结果。",
        ),
        (
            "且 n=141 小样本）",
            "且 n=262 仍为亚城市试点）",
        ),
        (
            "用 `h3.cell_to_boundary` 生成 141 个 R9 六边形面片",
            "用 `h3.cell_to_boundary` 生成 262 个 R9 六边形面片",
        ),
        (
            "模型表面在 67.4% 正类的极小窗口下仍偏乐观",
            "模型表面在 63.0% 正类的 Option B 窗口下仍偏乐观",
        ),
        (
            "141 → 4845 → 6909；自适应 = 34.4× 固定 R9 = 70.1% 均匀 R11（比率 0.701）",
            "262 → 7222 → 12838；自适应 = 56.3% 均匀 R11（比率 0.563；145/262 R9 父格被细化）",
        ),
        (
            "（564 行 = 141 单元 × 4 情景）",
            "（1048 行 = 262 单元 × 4 情景）",
        ),
        (
            "训练表 `data/processed/nyc_h3_cells.parquet` 的 141 个单元 `rainfall_mm_h` 全部为 **75.0**",
            "训练表 `data/processed/nyc_h3_cells.parquet` 的 262 个单元 `rainfall_mm_h` 全部为 **75.0**",
        ),
        (
            "§5.1 的 `n=141` 表只覆盖 Lower Manhattan 极小窗口",
            "§5.1 的 `n=262` Option B 表覆盖论文 Lower Manhattan bbox",
        ),
        (
            "扩展窗口正类占比 47.5%（正 454 / 502，近均衡），小窗口 67.4%（多数类为正）",
            "扩展窗口正类占比 47.5%（正 454 / 502，近均衡），小窗口 63.0%（多数类为正）",
        ),
        (
            "小窗口 0.781 > 0.662（恒判正）、扩展窗口 0.821 > 0.525（恒判负）",
            "小窗口 0.809 > 0.629（恒判正）、扩展窗口 0.821 > 0.525（恒判负）",
        ),
        (
            "小窗口 F1 亦超过 always-positive（0.822 > 0.794）",
            "小窗口 F1 亦超过 always-positive（0.846 > 0.762）",
        ),
        (
            "留出 pooled ROC-AUC：小窗口 0.780、扩展窗口 0.883；AP：小窗口 0.805（基线 0.674）、扩展窗口 0.812（基线 0.475）",
            "留出 pooled ROC-AUC：小窗口 0.847、扩展窗口 0.883；AP：小窗口 0.851（基线 0.630）、扩展窗口 0.812（基线 0.475）",
        ),
        (
            "留出 ROC-AUC（0.780 / 0.883）与 AP（0.805 / 0.812）均高于各自随机基线（0.674 / 0.475）",
            "留出 ROC-AUC（0.847 / 0.883）与 AP（0.851 / 0.812）均高于各自随机基线（0.630 / 0.475）",
        ),
        (
            "小窗口（67.4% 正类，7 块）模型在 accuracy/F1 上**均超过**恒判正基线（0.781 > 0.662、0.822 > 0.794）",
            "小窗口（63.0% 正类，12 块）模型在 accuracy/F1 上**均超过**恒判正基线（0.809 > 0.629、0.846 > 0.762）",
        ),
        (
            "小窗口 pooled ROC-AUC 0.780 / AP 0.805（随机基线 0.674）",
            "小窗口 pooled ROC-AUC 0.847 / AP 0.851（随机基线 0.630）",
        ),
        (
            "开放标签 H3+ML + 空间块 CV 已产生两个试点（LM smoke `n=141`、扩展窗口 `n=956`）",
            "开放标签 H3+ML + 空间块 CV 已产生两个试点（LM Option B `n=262`、扩展窗口 `n=956`）",
        ),
        (
            "小窗口 accuracy/F1（0.781/0.822）**超过**多数类（恒判正）平凡基线（0.662/0.794）",
            "小窗口 accuracy/F1（0.809/0.846）**超过**多数类（恒判正）平凡基线（0.629/0.762）",
        ),
        (
            "小窗口 ROC-AUC 0.780 / AP 0.805（随机基线 0.674）",
            "小窗口 ROC-AUC 0.847 / AP 0.851（随机基线 0.630）",
        ),
        (
            "类别失衡（修订后：小窗口 67.4% 正类 → 模型 accuracy/F1 均超恒判正基线；扩展窗口 47.5% 正类 → accuracy/F1 均超基线）",
            "类别失衡（Option B：小窗口 63.0% 正类 → 模型 accuracy/F1 均超恒判正基线；扩展窗口 47.5% 正类 → accuracy/F1 均超基线）",
        ),
        (
            "小样本块不均（小窗口仅 7 块分 5 折）",
            "小样本块不均（小窗口 12 块分 5 折）",
        ),
        (
            "本报告是仓库 **live Lower Manhattan open-data smoke** 的教师向（teacher-like）过程说明",
            "本报告是仓库 **live Lower Manhattan open-data Option B（n=262）** 的教师向（teacher-like）过程说明",
        ),
        (
            "（c）** 全拟合模型分 `PFI_h(c,r)`（合成 ida_like 情景 r=75 mm/h，均值 0.677；**全拟合模型输出，非留出验证图**）",
            "（c）** **deployment_full** 模型分 `PFI_h(c,r)`（合成 ida_like 情景 r=75 mm/h；**全量重拟合部署模型，非留出验证图**）",
        ),
    ]
    for a, b in cluster:
        if a in t:
            t = t.replace(a, b)
            print("report OK cluster:", a[:50])
        else:
            print("report MISS cluster:", a[:50])

    # Source ablation table LM column — update composite row and related
    t = t.replace(
        "| composite（max） | 95 / 454 | 0.780 / 0.883 | 0.798 / 0.883 | 0.822 / 0.819 |",
        "| composite（max） | 165 / 454 | 0.847 / 0.883 | 0.831 / 0.883 | 0.846 / 0.819 |",
    )
    t = t.replace(
        "小窗口 DEP-only（0.792）高于 composite pooled（0.780）",
        "小窗口 DEP-only（0.802）接近 composite pooled（0.847）",
    )
    t = t.replace(
        "去掉海岸距离预测变量 `dist_stream_m` 判别不变（扩展窗口 0.887 vs composite 0.883；小窗口 0.783 vs 0.780）",
        "去掉海岸距离预测变量 `dist_stream_m` 判别不变（扩展窗口 0.887 vs composite 0.883；小窗口 0.855 vs 0.847）",
    )

    # Block sensitivity LM rows
    t = t.replace(
        "| LM | 1（R8） | 27 | 0.750 | 0.650 | 0.809 | 0.864 | −0.053 |",
        "| LM | 1（R8） | 48 | 0.829 | 0.839 | 0.809 | 0.848 | 0.373 |",
    )
    t = t.replace(
        "| LM | 2（R7） | 7 | 0.780 | 0.798 | 0.781 | 0.822 | 0.048 |",
        "| LM | 2（R7） | 12 | 0.847 | 0.831 | 0.809 | 0.846 | 0.227 |",
    )
    t = t.replace(
        "| LM | 3（R6） | 3 | 0.697 | 0.586 | 0.840 | 0.899 | −0.319 |",
        "| LM | 3（R6） | 4 | 0.790 | 0.815 | 0.854 | 0.620 | — |",
    )
    t = t.replace(
        "小窗口不稳**：fold-mean ROC-AUC 在 R8=0.650、R7=0.798、R6=0.586 间波动，R² 在 R8/R6 转负（−0.053/−0.319）→ 小窗口「0.781 ± 0.123」确如审稿人所言是**不稳定小样本估计**",
        "Option B 后小窗口更稳**：pooled ROC-AUC 在 R8=0.829、R7=0.847、R6=0.790；fold-mean 亦不再出现 R6 崩塌式 0.586 → 「0.809 ± 0.046」仍应视为亚城市试点估计",
    )

    # Long SLR note in §5.1 — keep as historical, prepend Option B placeholder updated later after SLR rerun
    old_slr_note = (
        "SLR 敏感性（`outputs/slr_sensitivity.json`）：** 用 2050 海平面上升层重跑后，小窗口正类 95→98（67.4%→69.5%）、"
        "pooled ROC-AUC 0.780→0.741，精确复现上一版主表数字，证明修复前确系误用 2050 层；扩展窗口正类 454→475（47.5%→49.7%）、"
        "pooled ROC-AUC 0.883→0.875。两情景下所有实质结论不变，故结果不依赖 DEP 海平面情景选择。**"
    )
    new_slr_note = (
        "SLR 敏感性（`outputs/slr_sensitivity.json`）：** 见 §5.1 后文与审计 §14；Option B（n=262）重跑后数字以该 JSON 为准。"
        "（历史：pre-Option-B n=141 时曾报告 67.4%→69.5%、ROC-AUC 0.780→0.741。）扩展窗口 454→475（47.5%→49.7%）、"
        "pooled ROC-AUC 0.883→0.875。两情景下实质结论不变。**"
    )
    if old_slr_note in t:
        t = t.replace(old_slr_note, new_slr_note)
        print("report OK: SLR note placeholder")
    else:
        print("report MISS: SLR note")

    # Historical note for the long C1/M4 paragraph
    old_hist = (
        "**注意：2026-08-23 审稿修订（C1：剔除 DEP category 3 海岸高潮位、C5：负对照分组修复、M5：ponding 基线去泄漏）后，"
        "正类占比从 80.1% 降至 69.5%，模型 accuracy/F1 从“低于多数类基线”变为“超过多数类基线”；"
        "2026-08-24 审稿修订（M4）进一步把 DEP 主层从 2050 海平面上升改回当前海平面 \"Moderate Flood with Current Sea Levels\" 层，"
        "正类占比由 69.5% 微调至 67.4%，相应指标同步更新（ROC-AUC 0.741→0.780、accuracy 0.808→0.781、F1 0.864→0.822），结论不变。**"
    )
    new_hist = (
        "**历史注记（pre-Option-B，n=141）：** 2026-08-23 C1/C5/M5 与 2026-08-24 M4 曾把 smoke 表正类从 80.1%→69.5%→67.4%、"
        "并更新 ROC-AUC/accuracy/F1。**当前真相是 Option B n=262（正类 63.0%，acc 0.809，F1 0.846，ROC-AUC 0.847），"
        "勿把上述 n=141 数字当作现行主表。**"
    )
    if old_hist in t:
        t = t.replace(old_hist, new_hist)
        print("report OK: hist note")
    else:
        print("report MISS: hist note")

    # AP row if present
    t = t.replace(
        "| 留出 AP（pooled） | **0.805**（随机基线 = 正类占比 0.674） |",
        "| 留出 AP（pooled） | **0.851**（随机基线 = 正类占比 0.630） |",
    )
    t = t.replace(
        "| F1 mean ± std |",
        "| F1 mean ± std |",
    )
    # Try F1 row specifically
    import re

    t = re.sub(
        r"\| F1 mean ± std \| [0-9. ±]+ \|",
        "| F1 mean ± std | 0.846 |",
        t,
        count=1,
    )
    t = re.sub(
        r"\| R² mean ± std \| [0-9. ±\-]+ \|",
        "| R² mean ± std | 0.227 ± 0.196 |",
        t,
        count=1,
    )

    # Adaptive counts if still old
    t = t.replace("| n_adaptive_mixed | 4,845 |", "| n_adaptive_mixed | 7,222 |")
    t = t.replace("| n_uniform_fine (R11) | 6,909 |", "| n_uniform_fine (R11) | 12,838 |")
    t = t.replace("| adaptive_cell_count_ratio | 0.701 |", "| adaptive_cell_count_ratio | 0.563 |")
    t = t.replace("| n_adaptive | 4845 |", "| n_adaptive | 7222 |")
    t = t.replace("| n_uniform_fine | 6909 |", "| n_uniform_fine | 12838 |")

    p.write_text(t, encoding="utf-8")
    print("wrote", p)


def patch_manuscript() -> None:
    p = ROOT / "docs" / "paper" / "manuscript.md"
    t = p.read_text(encoding="utf-8")

    # SLR sentence in §2
    old = (
        "Re-running the target with the 2050 layer shifts prevalence (Lower Manhattan 67.4% to 69.5%; "
        "expanded 47.5% to 49.7%) and pooled ROC-AUC (0.780 to 0.741; 0.883 to 0.875) without changing "
        "any substantive conclusion, so the results are not an artefact of the sea-level scenario "
        "selected for the stormwater layer."
    )
    new = (
        "Re-running the target with the 2050 layer is reported as a sensitivity "
        "(`outputs/slr_sensitivity.json`); under Option B (n = 262) the prevalence and pooled "
        "ROC-AUC shifts are recorded there and do not change any substantive conclusion, so the "
        "results are not an artefact of the sea-level scenario selected for the stormwater layer. "
        "(Pre-revision n = 141 smoke figures 67.4%→69.5% / 0.780→0.741 are historical only.)"
    )
    if old in t:
        t = t.replace(old, new)
        print("ms OK: SLR sentence")
    else:
        print("ms MISS: SLR sentence")

    # Table 7 composite row + discussion
    t = t.replace(
        "| Composite (max) | 95 / 454 | 0.780 / 0.883 | 0.798 / 0.883 | 0.822 / 0.819 |",
        "| Composite (max) | 165 / 454 | 0.847 / 0.883 | 0.831 / 0.883 | 0.846 / 0.819 |",
    )
    t = t.replace(
        "| DEP-only (polygon area) | 40 / 231 | 0.792 / 0.811 | 0.800 / 0.815 | 0.534 / 0.455 |",
        "| DEP-only (polygon area) | 74 / 231 | 0.802 / 0.811 | 0.789 / 0.815 | 0.496 / 0.455 |",
    )
    t = t.replace(
        "| 311-only (crowd reports) | 84 / 367 | 0.748 / 0.848 | 0.746 / 0.849 | 0.742 / 0.709 |",
        "| 311-only (crowd reports) | 141 / 367 | 0.864 / 0.848 | 0.826 / 0.849 | 0.756 / 0.709 |",
    )
    t = t.replace(
        "| 311 + HWM | 84 / 369 | 0.748 / 0.846 | 0.746 / 0.846 | 0.742 / 0.714 |",
        "| 311 + HWM | 141 / 369 | 0.864 / 0.846 | 0.826 / 0.846 | 0.756 / 0.714 |",
    )
    t = t.replace(
        "| Composite without dist_stream_m | 95 / 454 | 0.783 / 0.887 | 0.785 / 0.888 | 0.869 / 0.818 |",
        "| Composite without dist_stream_m | 165 / 454 | 0.855 / 0.887 | 0.829 / 0.888 | 0.855 / 0.818 |",
    )
    t = t.replace(
        "in the smaller pilot the corresponding values are 0.792 and 0.748 against 0.780",
        "in the smaller pilot the corresponding values are 0.802 and 0.864 against 0.847",
    )

    # §5.4 limitations paragraph with 67.4% / seven blocks / 0.048
    old_lim = (
        "The smaller pilot is 67.4% positive and distributes seven H3 blocks across five folds "
        "(per-fold test size 21–49, with some folds containing a single block); the expanded pilot "
        "uses 28 blocks with larger per-fold test sets. Block-size sensitivity (Section 4.9) shows "
        "the expanded pilot's ranking discrimination is stable across R8/R7/R6 blocking "
        "(pooled ROC-AUC 0.888/0.883/0.873), but the smaller pilot's fold-mean ROC-AUC ranges from "
        "0.586 to 0.798 across block sizes, and the composite target is positively spatially "
        "autocorrelated (Moran's I 0.224–0.433); the smaller pilot's estimate is therefore treated "
        "as block-size dependent. The evidence-score R² is 0.048 in the smaller pilot and 0.333 in "
        "the expanded pilot"
    )
    new_lim = (
        "The smaller Option B pilot is 63.0% positive and distributes 12 H3 blocks across five folds; "
        "the expanded pilot uses 28 blocks with larger per-fold test sets. Block-size sensitivity "
        "(Section 4.9) shows the expanded pilot's ranking discrimination is stable across R8/R7/R6 "
        "blocking (pooled ROC-AUC 0.888/0.883/0.873), and the Option B Lower Manhattan pooled ROC-AUC "
        "is 0.829/0.847/0.790; the composite target is positively spatially autocorrelated "
        "(Moran's I 0.385–0.433). The evidence-score R² is 0.227 in the smaller pilot and 0.336 in "
        "the expanded pilot"
    )
    if old_lim in t:
        t = t.replace(old_lim, new_lim)
        print("ms OK: limitations")
    else:
        print("ms MISS: limitations")

    t = t.replace(
        "Adaptive refinement was selected with in-sample full-fit scores",
        "Adaptive refinement was selected with in-sample deployment_full scores",
    )

    p.write_text(t, encoding="utf-8")
    print("wrote", p)


if __name__ == "__main__":
    patch_report()
    patch_manuscript()
