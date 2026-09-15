# -*- coding: utf-8 -*-
"""One-shot generator: docs/paper/report.md from paper_results.json + live CSVs."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def f3(x: float) -> str:
    return f"{float(x):.3f}"


def main() -> None:
    d = json.loads((ROOT / "outputs" / "paper_results.json").read_text(encoding="utf-8"))
    lm = d["lower_manhattan"]
    ex = d["manhattan_expanded"]
    scv = lm["spatial_cv"]
    b = lm["baselines"]
    folds = pd.read_csv(ROOT / "models" / "nyc_smoke" / "spatial_cv_folds.csv")
    jac = pd.read_csv(ROOT / "outputs" / "jaccard_by_resolution.csv")
    fn = d["floodnet"]["pilots"][0]
    fn2 = d["floodnet"]["pilots"][1]
    ada = d["adaptive"]["rows"][0]
    neg = d["negative_control"]

    fold_rows = []
    for _, r in folds.iterrows():
        fold_rows.append(
            f"| {int(r.fold_id)} | {int(r.n_train)} | {int(r.n_test)} | "
            f"{int(r.n_positive_test)}/{int(r.n_negative_test)} | "
            f"{r.accuracy:.3f} | {r.f1:.3f} | {r.r2:+.3f} | {r.mae:.3f} | "
            f"{r.roc_auc:.3f} | {r.pr_auc:.3f} |"
        )

    jac_rows = []
    for _, r in jac.iterrows():
        jac_rows.append(
            f"| R{int(r.coarse_res)} | {r.aggregation} | {r.jaccard_soft:.3f} | "
            f"{r.jaccard_hard_median:.3f} "
            f"[{r.jaccard_hard_ci_low:.3f}, {r.jaccard_hard_ci_high:.3f}] | "
            f"{r.fine_parent_recall:.3f} | {r.coarse_precision:.3f} |"
        )

    pluvial_coastal_diff = float(neg["mean_score_pluvial_only"]) - float(
        neg["mean_score_coastal_only"]
    )

    report = f"""# 研究报告 / Research Report（深度自包含对照稿）

**主 HTML（自包含 Base64 图 + 内联 CSS，无 CDN）：** `docs/paper/report.html`（根目录 `report.html` 为逐字副本）  
**PDF：** `docs/paper/report.pdf`（Chrome headless；HTML 为规范源）  
**手稿对照：** `docs/paper/manuscript.md`（用户主线；2026-09-15 成熟化）  
**数值基线：** 仅来自 `outputs/paper_results.json` 与 live CSV；缺则标 **待补充**  
**GitHub：** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3  
**框架说明：** `docs/paper/framework_note.md`

---

## 术语总表 Terminology ledger

| 术语 Term | 括号释义 / Canonical meaning |
|-----------|------------------------------|
| Pluvial flood（城市内涝 / 雨洪） | 短时强降雨超过排水与入渗能力导致的地表积水；不同于潮汐/风暴潮主导的 coastal inundation |
| H3（Uber Hexagonal DGGS） | 六边形离散全球网格索引，支持父子分辨率嵌套 |
| Open evidence（开放证据） | 异构公开源：DEP 雨洪多边形（**模型导出** category 1–2）、官方 311 `76ig-c548`（2010–2014 Street Flooding (SJ)）、USGS Ida HWM（**观测**）；不是 PFIb |
| PFI_h(c,r) | 降雨条件 r 下单元 c 的正类 **model score**（未校准）；非特征重要性，也非 Svellingen 的 PFIb 聚合 |
| Spatial H3-block CV | 按粗分辨率 H3 父块 GroupKFold，整块留出 |
| Jaccard ladder | 细网格热点与粗网格热点的集合相似度（主指标 = area-weighted soft Jaccard，strict area budget） |
| Adaptive H3 | 用 deployment 全拟合分数筛选父单元并加密到 R11；仅计单元数，不宣称运行效率 |
| LM Option B | 论文 bbox 上开放数据试点 **n=262**；遗留 smoke 141 仅 QA |
| FloodNet held-out | 传感器事件严格留出诊断；**永不入训练标签** |
| Fail-closed | 缺层/NaN 直接中止，禁止静默填合成特征 |

---

## 1. 摘要 Abstract

本报告是仓库 **live Lower Manhattan open-data Option B（n=262）** 的教师向过程说明：对每张表/图交代**来龙去脉、如何读、意义、可下结论、不可下结论**。

在 H3 R9 上组装 **n_cells = 262**（bbox `[-74.02, 40.70, -73.97, 40.76]`）。主评价为 **spatial H3-block CV**（12 个 R7 块，5 折）：准确率 **{f3(scv['spatial_cv_accuracy_mean'])} ± {f3(scv['spatial_cv_accuracy_std'])}**，F1 **{f3(scv['spatial_cv_f1_mean'])}**；正类占比 **{lm['positive_prevalence']*100:.1f}%**；恒判正基线 accuracy **{f3(b['always_positive_mean_acc'])}**、F1 **{f3(b['always_positive_mean_f1'])}**，模型超过该基线。留出 pooled ROC-AUC **{f3(scv['spatial_cv_roc_auc_pooled'])}**、AP **{f3(scv['spatial_cv_pr_auc_pooled'])}**。扩展试点 n=956：acc **{f3(ex['spatial_cv']['spatial_cv_accuracy_mean'])} ± {f3(ex['spatial_cv']['spatial_cv_accuracy_std'])}**，F1 **{f3(ex['spatial_cv']['spatial_cv_f1_mean'])}**，pooled ROC-AUC **{f3(ex['spatial_cv']['spatial_cv_roc_auc_pooled'])}**。尺度损失（strict area budget）：R10→R9 mean soft Jaccard **0.227**，R10→R8 mean **0.136**。自适应相对均匀 R11 单元数比 **≈0.563**（145/262 父单元加密 → 7,222 vs 12,838）。FloodNet 为严格留出诊断（LM ROC-AUC {f3(fn['roc_auc'])}，23 传感器单元）。

> **历史注记：** 修订前曾用 n=141 smoke 主表。该数字**不是**当前真相。

**诚实缺口（待补充）：** (1) 观测事件降雨仍阻塞，合成常数情景下 within-cell PFI_h 极差=0；(2) LM ≠ citywide；(3) 作者姓名/ORCID/CRediT；(4) DEP 官方 geospatial 导出若可机读下载后替换镜像。

---

## 2. 背景与写作架构

### 2.1 问题

城市 pluvial screening 需要可扩展空间表示、可更新证据、以及不因空间自相关虚高的评价。H3 提供嵌套六边形，但既有强对照（Svellingen et al. 2026 IJDRR）主叙事是 **PFIb→H3 聚合与沟通**，不是开放标签下的空间诚实学习协议。

### 2.2 文献对照（本轮 web survey）

| 文献 | 对本稿的作用 |
|------|-------------|
| Svellingen et al. 2026 IJDRR | 模仿章节骨架；**禁止**抄其 Jaccard 0.14 / 98% 效率 / PFIb |
| Li et al. 2022 IJGI 六边形多尺度洪水 | 支持 DGGS 多分辨率织物角色 |
| Bersabe & Jun 2025 Seoul pluvial ML | 开放因子 ML 地图对照；通常缺 H3-block CV + 自适应 + 降雨诚实边界 |
| Spatial CV / h3sdm_spatial_cv 等 | 支持父块留出评价 |
| Agonafir et al. NYC 311 | 众包标签偏差文献 |

### 2.3 创新主张（贡献是协议，不是工具栈）

见 `docs/paper/framework_note.md`：开放异构标签保持区分、H3-block 空间 CV、面积预算 soft Jaccard、deployment 分数驱动自适应、`PFI_h(c,r)` 定义（当前降雨响应平坦）。

---

## 3. 数据与方法（过程可读）

### 3.1 研究区

- LM Option B：约 74.02–73.97°W，40.70–40.76°N，**n=262**。  
- 扩展：约 74.03–73.94°W，40.68–40.80°N，**n=956**。  
两者均为试点，**不是全市**。

### 3.2 Live 图层

| 图层 | 角色 | 诚实标签 |
|------|------|----------|
| USGS 3DEP DEM | 地形特征 | 官方服务导出 |
| DEP stormwater polygons cat.1–2 | 模型导出证据 | FeatureServer 镜像，`verified=false` |
| 官方 311 `76ig-c548` 2010–2014 | 众包证据 | `official_identity_verified=true` |
| USGS Ida HWM | 观测点证据 | DOI 官方 |
| FEMA Sandy | 海岸叠置诊断 | **永不训练** |
| FloodNet aq7i-eu5q + kb2e-tjy3 | 传感器留出诊断 | **永不训练** |
| `event_rainfall.tif` | 合成常数 75 mm/h | **非雷达/雨量计** |

### 3.3 H3 分辨率角色

| 用途 | 分辨率 |
|------|--------|
| 训练/评价 | R9 |
| Jaccard 细网格 | R10（n_fine=1857） |
| Jaccard 上卷 | R9 / R8 |
| 自适应加密 | 选中父单元 → R11 |
| 空间块 | 主协议 R7（k=2）；敏感性 R8/R6 |

### 3.4 模型与评价

- GBM 分类器 + 证据分回归器（80 trees, depth 4, lr 0.08, seed 42）。  
- 主指标：H3-block GroupKFold；常量类基线必须同报。  
- 评价后 **deployment_full** 全量重拟合仅用于图 2(c) 与自适应筛选。  
- 组装 **fail-closed**。

### 3.5 PFI_h(c,r)

\\[
\\mathrm{{PFI}}_h(c,r)=\\widehat{{P}}(Y_c=1\\mid X_c,r)
\\]
当前 r 恒定 → 情景表 within-cell range = 0 → **不宣称降雨条件判别力**。

#### 图 1 · `docs/paper/figures/workflow_schematic.png`

**来龙去脉：** SciencePlots + Times New Roman 概念工作流；`plot_workflow_schematic` 生成，无数据依赖。  
**如何读：** 左→右：开放输入 → H3 组装 → 分块学习/评价 → 诊断输出；Sandy 为虚线旁路。  
**意义：** 一眼看清协议边界。  
**结论（允许）：** 框架把证据组装、空间 CV、尺度诊断、自适应绑在同一网格上。  
**结论（禁止）：** 把示意图当作已验证全市产品。

---

## 4. 过程 Process

1. 下载/校验 `data/raw/nyc/`，写 manifest。  
2. `build_nyc_h3.py --no-fixtures` → `data/processed/nyc_h3_cells.parquet`。  
3. 训练/诊断 → `models/nyc_smoke/*`、`models/nyc_expanded/*`、`outputs/*`。  
4. 冻结注册表 `outputs/paper_results.json`。  
5. `scripts/make_figures.py`（SciencePlots + TNR）→ `docs/paper/figures/`。  
6. `scripts/build_paper_report_html.py` / `build_manuscript_html.py` → 自包含 HTML；Chrome → PDF。

---

## 5. 结果 Results（仅 live 产物）

### 表 1 · 空间 CV 汇总（主分块评价）

**来源：** `outputs/paper_results.json` → `lower_manhattan.spatial_cv` + `baselines`；折表 `models/nyc_smoke/spatial_cv_folds.csv`

| Metric | Value |
|--------|-------|
| n_cells | {lm['n_cells']} |
| spatial_cv_n_folds / n_blocks | {int(scv['spatial_cv_n_folds'])} / {int(scv['spatial_cv_n_blocks'])} |
| accuracy mean ± std | {f3(scv['spatial_cv_accuracy_mean'])} ± {f3(scv['spatial_cv_accuracy_std'])} |
| F1 mean | {f3(scv['spatial_cv_f1_mean'])} |
| R² mean ± std | {f3(scv['spatial_cv_r2_mean'])} ± {f3(scv['spatial_cv_r2_std'])} |
| MAE mean | {f3(scv['spatial_cv_mae_mean'])} |
| random_split_val_accuracy（诊断） | {f3(scv['random_split_val_accuracy'])} |
| 正类占比 | {lm['positive_prevalence']:.4f} |
| 恒判正 accuracy / F1 | {f3(b['always_positive_mean_acc'])} / {f3(b['always_positive_mean_f1'])} |
| 恒判负 accuracy | {f3(b['always_negative_mean_acc'])} |
| 模型是否超过多数类 acc / f1 | **是 / 是** |
| pooled ROC-AUC / AP | **{f3(scv['spatial_cv_roc_auc_pooled'])} / {f3(scv['spatial_cv_pr_auc_pooled'])}** |
| evaluation_fit_rows / deployment_fit_rows | {lm['evaluation']['fit_rows']} / {lm['deployment']['fit_rows']} |

**来龙去脉：** 训练脚本按 R7 父块 GroupKFold 留出；折均写入 metadata/registry；常量基线按同一折表聚合。这是报告与手稿优先引用的主表。  
**如何读：** 先看正类占比（63.7%），再看恒判正基线（0.637 / 0.769），最后才看模型（0.820 / 0.858）。ROC-AUC/AP 是阈值无关排序指标。  
**意义：** 在类别失衡试点上，离开平凡基线谈 accuracy/F1 没有意义。  
**结论（允许）：** Option B 上模型超过恒判正；存在中等排序判别。  
**结论（禁止）：** 全市技能；用随机划分替换空间 CV；把 R² 当成物理水深拟合。

### 表 2 · 逐折明细

| fold | n_train | n_test | +/− | accuracy | f1 | r2 | mae | roc_auc | pr_auc |
|------|---------|--------|-----|----------|-----|-----|-----|---------|--------|
{chr(10).join(fold_rows)}

**来龙去脉：** 每折留出若干 R7 块；折间正负比不均导致跳动（尤其 Fold1 正类极高）。  
**如何读：** 同时看 n_test 与正负计数，再读 accuracy/F1；末列 ROC/PR 是折内排序。  
**意义：** 必须报 mean±std，不能挑最好一折。  
**结论：** 均值有效，但外部效度受小样本与块不均限制。

#### 图 2 · `docs/paper/figures/spatial_maps.png`

**来源：** `nyc_h3_cells.parquet` + `spatial_cv_oof_predictions.csv` + `pfi_h_scenarios.parquet` + DEM/水系底图。  
**来龙去脉：** 三面板同 262 格支撑：(a) 开放证据分；(b) 留出 OOF 分；(c) deployment 全拟合 PFI_h（合成 Ida-like）。  
**如何读：** 同色标 0–1；(a) 双峰；(b)(c) 更平滑；(c) **不是**验证结果。  
**意义：** “先直观后统计”的结果入口。  
**结论（允许）：** 视觉检视；与表 1 叙事一致。  
**结论（禁止）：** 把 panel (c) 当第三种验证；从图面高低外推全市。

#### 图 3 · `docs/paper/figures/source_evidence_maps.png`

**来龙去脉：** 把 DEP / 311 / HWM / composite 拆成四面板，证明“源保持区分”发生在训练表而非仅文档。  
**如何读：** (a)(d) 0–1；(b)(c) 计数；LM 内 Ida 点为空是数据事实。  
**意义：** 回应“合成标签掩盖异质来源”质疑。  
**结论（允许）：** 三源空间部分重叠；composite=max。  
**结论（禁止）：** 把 DEP 当观测洪水。

#### 图 4 · `docs/paper/figures/spatial_cv_folds.png`

**来龙去脉：** 由表 2 绘制 Accuracy/F1 成对点 + Mean±SD；水平线为恒判正/恒判负基线。  
**如何读：** 折间跳动是信号，不是噪声。  
**意义：** 把基线对照可视化。  
**结论：** 与表 1/2 一致；仍是 n=262 试点。

### 表 3 · Jaccard 尺度损失阶梯

**来源：** `outputs/jaccard_by_resolution.csv`（`budget_match_mode=strict_area_budget`；主指标 soft Jaccard）

| Coarse | Agg | Soft Jaccard | Hard median [95% CI] | Fine-parent recall | Coarse precision |
|--------|-----|--------------|----------------------|--------------------|------------------|
{chr(10).join(jac_rows)}

**来龙去脉：** 在原生 R10 证据上按 10% 面积预算定义热点，再上卷到 R9/R8；图 6b 与本表同 CSV，禁止图中重算。  
**如何读：** 主看 mean 聚合：R9=0.227，R8=0.136；max/p90 更高是因为极值保留，不是“更正确”。  
**意义：** 粗化会抹掉细热点——这是表示代价，不是软件 bug。  
**结论（允许）：** 开放证据下存在实质性尺度损失。  
**结论（禁止）：** “复现了 Svellingen 的 0.14”。

#### 图 5 · `docs/paper/figures/multi_resolution_spatial.png`

**来龙去脉：** R10→R9→R8 mean rollup 的空间面；同色标看平滑。  
**如何读：** 从左到右斑块变大、对比变弱。  
**意义：** 表 3 的空间直觉。  
**结论：** 粗化平滑局部极值；与 soft Jaccard 下降同向。

#### 图 6 · `docs/paper/figures/resolution_effects.png`

**来龙去脉：** (a) 分数分布小提琴；(b) soft Jaccard 热力/柱状读自 CSV。  
**如何读：** (a) 方差压缩；(b) 数值必须与表 3 逐位一致。  
**意义：** 分布压缩 + 热点集合损失的双证据。  
**结论：** 数值与表 3 一致；图不重算 Jaccard。

### 表 4 · 自适应 vs 均匀细网格（单元数）

| Representation | Cell count |
|---|---|
| Fixed R9 | {ada['adaptive_n_coarse']} |
| Adaptive R9/R11 | {ada['adaptive_n_adaptive']} |
| Uniform R11 | 12838 |

筛选：分数 ≥0.8 分位或不确定区间，再扩一环；**deployment_full** 入样分数。

**来龙去脉：** 自适应只改表示密度，不改 R9 模型。  
**如何读：** 7,222 / 12,838 ≈ 56.3%。  
**意义：** 表示压缩可行；未测 runtime/热点保留。  
**结论（允许）：** 单元数减少。  
**结论（禁止）：** 全市算力节省、热点无损失。

#### 补充图 S1 · `docs/paper/figures/supplementary/jaccard_by_resolution.png`

与表 3 同 CSV 的补充可视化。

#### 补充图 S2 · `docs/paper/figures/supplementary/adaptive_ablation.png`

与表 4 同口径的柱状对比。

### 表 5 · Sandy 海岸叠置诊断（OOF 分数）

| Statistic | Value |
|---|---|
| Coastal / pluvial / both / coastal-only / neither | {int(neg['n_coastal'])} / {int(neg['n_pluvial'])} / {int(neg['n_both'])} / {int(neg['n_coastal_only'])} / {int(neg['n_neither'])} |
| Mean OOF coastal-only / pluvial-only | {f3(neg['mean_score_coastal_only'])} / {f3(neg['mean_score_pluvial_only'])} |
| Pluvial − coastal OOF difference | {f3(pluvial_coastal_diff)} |

**来龙去脉：** Sandy **不是**训练标签；比较的是 OOF 模型分，不是目标分（海岸-only 目标分恒为 0）。  
**结论（允许）：** 模型不完全由海岸位置驱动，但海岸-only 仍获非零分。  
**结论（禁止）：** “已排除沿海混淆”。

### 表 6 · FloodNet 严格留出诊断

| Pilot | Sensor cells | Event cells | ROC-AUC | AP |
|-------|--------------|-------------|---------|-----|
| LM | {fn['n_study_cells_with_sensor']} | {fn['n_study_cells_with_event']} | {f3(fn['roc_auc'])} | {f3(fn['average_precision'])} |
| Exp | {fn2['n_study_cells_with_sensor']} | {fn2['n_study_cells_with_event']} | {f3(fn2['roc_auc'])} | {f3(fn2['average_precision'])} |

**来龙去脉：** 传感器足迹稀疏；诊断弱且不可外推。  
**结论（禁止）：** 把 FloodNet 写成外部验证成功或训练标签。

### 表 7 · 扩展试点摘要

| Metric | Expanded n=956 |
|--------|----------------|
| Prevalence | {ex['positive_prevalence']:.4f} |
| Acc ± SD | {f3(ex['spatial_cv']['spatial_cv_accuracy_mean'])} ± {f3(ex['spatial_cv']['spatial_cv_accuracy_std'])} |
| F1 | {f3(ex['spatial_cv']['spatial_cv_f1_mean'])} |
| Pooled ROC-AUC / AP | {f3(ex['spatial_cv']['spatial_cv_roc_auc_pooled'])} / {f3(ex['spatial_cv']['spatial_cv_pr_auc_pooled'])} |
| Always-pos acc / F1 | {f3(ex['baselines']['always_positive_acc_mean'])} / {f3(ex['baselines']['always_positive_f1_mean'])} |
| Majority-neg acc | {f3(ex['baselines']['majority_acc_mean'])} |

**意义：** 曼哈顿内尺度放大检查，不是独立外域验证。

---

## 6. 讨论要点（教师向）

1. **超过平凡基线**改变了“有没有学到东西”的读法，但仍是亚城市试点。  
2. **尺度损失**与 **自适应单元压缩**回答的是表示问题，不是预报问题。  
3. **源消融**显示 311-only 也能排序，减轻“只会复读 DEP 模型图”的担忧，但不能证明标签语义完全有效。  
4. **降雨响应平坦**是当前数据事实，不是写作疏漏。

---

## 7. 局限与待补充

1. 作者姓名 / 单位 / ORCID / CRediT：**待补充**  
2. 观测事件降雨与非零 PFI_h(r) 响应：**待补充**  
3. Citywide 评价：**未做**  
4. DEP 官方 geospatial 机读替换镜像：**可选待补充**  
5. 更密 FloodNet / 深度阈值：**科学扩展，非 P0 工程尾巴**

---

## 8. 复现清单（最短路径）

```text
.venv\\Scripts\\python.exe -m pytest -q
.venv\\Scripts\\python.exe scripts\\make_figures.py
.venv\\Scripts\\python.exe scripts\\build_manuscript_html.py
.venv\\Scripts\\python.exe scripts\\build_paper_report_html.py
```

核对：`outputs/paper_results.json` 与本文表 1/3/7 数值一致；图 6b 与 `jaccard_by_resolution.csv` 一致。

---

*Generated for Option B freeze · registry {d['generated_utc']} · fail_closed={d['fail_closed']} · seed={d['random_seed']}*
"""

    out = ROOT / "docs" / "paper" / "report.md"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out} chars={len(report)} lines={report.count(chr(10))+1}")


if __name__ == "__main__":
    main()
