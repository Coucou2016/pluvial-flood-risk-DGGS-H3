# 研究报告 / Research Report（深度自包含对照稿）

**主 HTML（自包含 Base64 图 + 内联 CSS，无 CDN）：** `docs/paper/report.html`（根目录 `report.html` 为逐字副本）  
**PDF：** `docs/paper/report.pdf`（Chrome headless；HTML 为规范源）  
**手稿对照：** `docs/paper/manuscript.md`  
**数值基线：** 仅来自 `outputs/` 与 `models/nyc_smoke/` 的 live 产物；缺则标 **待补充**  
**GitHub（已公开，勿重复 create）：** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3  
**ChatGPT 公开 URL 索引：** `artifacts/chatgpt_review_index.md`（blob + raw）；短粘贴包 `artifacts/chatgpt_paste_github_urls_R6_R10.md`；R6–R10 正文 `artifacts/chatgpt_paste_R6.md`–`R10.md`（另保留 R1–R5）。**Paper/report 边界（R6）：** 手稿 `manuscript.md` 已剥离本地路径与 Cursor/ChatGPT 过程；本报告保留路径、复现与来龙去脉。验收：`artifacts/acceptance_R6_R10.md`。

---

## 术语总表 Terminology ledger（首次出现均给出括号释义）

| 术语 Term | 括号释义 / Canonical meaning |
|-----------|------------------------------|
| Pluvial flood（城市内涝 / 雨洪） | 短时强降雨超过排水与入渗能力导致的地表积水；不同于潮汐/风暴潮主导的 coastal inundation（沿海淹没） |
| H3（Uber Hexagonal DGGS） | Discrete Global Grid System（离散全球网格系统）中的六边形索引，支持父子分辨率嵌套 |
| DGGS（离散全球网格） | 把地球表面剖分为可索引单元的规则网格框架 |
| Open evidence（开放证据） | 异构公开源：DEP 雨洪多边形（**模型导出**，category 1–2，已剔除 category 3 海岸高潮位）、311 街道积水点（**arcgis_streetfloodtime 2010–2014 快照**）、USGS Ida HWM（**观测**）；**不是**保险公司 PFIb，也不是单一 "observed ground truth" |
| PFIb（building-level Pluvial Flood Index） | 7Analytics / Svellingen 等所用建筑级雨洪指数（保险损害驱动）；本项目**不使用** |
| PFI_h(c,r) | 模型在降雨条件 \(r\) 下对六边形单元 \(c\) 的正类 **model score**（未校准，非概率）；**不是**特征重要性，也**不是** PFIb（注意：Svellingen 等也用 `PFI_h` 表示其 H3 聚合后的 PFIb；本项目的 `PFI_h(c,r)` 是独立定义，二者符号同名但语义不同）。因训练降雨恒为常数，当前 \(r\) 响应平坦（within-cell range=0） |
| Spatial H3-block CV（空间 H3 块交叉验证） | 按粗分辨率 H3 父块分组的 GroupKFold，整块留出，降低地理泄漏（spatial leakage） |
| Random split（随机划分） | 近似 i.i.d. 划分；本报告仅作诊断，不得替代空间 CV |
| Jaccard ladder（Jaccard 阶梯） | 细分辨率热点集合与父级聚合热点的集合相似度，随分辨率与聚合方式变化 |
| MAUP（可变面元问题） | Modifiable Areal Unit Problem：分区尺度/边界改变可改变统计结论 |
| Adaptive H3（自适应 H3） | 用训练后分数筛选高风险父单元，再加密到细分辨率，以降低均匀细网格成本 |
| LM Option B（Lower Manhattan） | 论文 bbox 上的开放数据试点（`n_cells=262`），**≠ citywide**；遗留 smoke 141 仅 QA |
| assembly_mode=opendata | 训练表由观测开放图层组装（非 fixture 合成表） |
| fixture / synthetic demo | 管道 QA 用合成数据；**≠ science** |
| I2（观测事件降雨） | 计划接入 gauge/radar 事件降雨；当前仍阻塞，仅有合成常数 `event_raster` |
| Negative control（负对照） | FEMA Sandy 沿海淹没叠置检查；**永不作为训练标签** |
| SciencePlots | matplotlib 学术样式插件；本报告图使用 Times New Roman（TNR） |
| Trivial / constant baseline（平凡基线 / 常量基线） | 不做学习的“闭眼”预测（如恒判正类 always-positive、恒判负类 always-negative）；用于对照模型是否真的学到判别力；真多数类由 pooled 类别数推导 |

---

## 1. 摘要 Abstract

本报告是仓库 **live Lower Manhattan open-data Option B（n=262）** 的教师向（teacher-like）过程说明：不只贴图，而是交代每张表/图的**来龙去脉、如何读、意义、可下的结论、不可下的结论**。

在 H3 分辨率 R9 上组装 **n_cells = 262** 个六边形单元（Major Revision **Option B**：论文 Lower Manhattan bbox `[-74.02, 40.70, -73.97, 40.76]`；遗留 smoke 141 仅 QA），`assembly_mode=opendata`。主（**分块评价**）指标为 **spatial H3-block CV**：准确率均值 **0.820 ± 0.057**，F1 均值 **0.858**（来源：`outputs/paper_results.json` / `models/nyc_smoke/run_manifest.json`）。留出正类占比 **63.7%**，恒判正基线 accuracy **0.637**、F1 **0.769**，模型 **0.820 / 0.858 超过**该基线。留出 pooled ROC-AUC **0.848**、AP **0.855**。尺度损失用开放证据 **Jaccard ladder**（strict area budget + fractional membership; canonical CSV）：细 R10→粗 R9 **mean** soft Jaccard = **0.227**、R10→R8 **mean** soft Jaccard = **0.136**（不得写成“复现了 Svellingen 的 0.14”）。自适应相对均匀细网格（R11）单元数比 **adaptive_cell_count_ratio ≈ 0.563**。图 2(c) 与自适应仅使用 **deployment_full** 全量重拟合模型。FloodNet（`aq7i-eu5q`+`kb2e-tjy3`）已下载并做严格留出诊断（不入训练标签）。

> **历史注记（pre-Option-B，n=141 smoke）：** 修订前主表曾误用较小 smoke bbox（n=141，正类≈67.4%，acc≈0.781 / F1≈0.822 / ROC-AUC≈0.780）。该数字**不是**当前 Option B 真相，仅作审计轨迹。

**诚实缺口（待补充）：** (1) I2 观测事件降雨仍阻塞，`rainfall_source=event_raster` 为合成常数钩子；(2) `outputs/pfi_h_scenarios.parquet` 四情景（25/40/75/100 mm/h）下，**单元内 PFI_h 极差 = 0**，情景均值同为 ≈0.6774，故**不宣称**已观察到降雨条件判别力；(3) LM ≠ citywide；(4) ChatGPT 浏览器 MCP 本会话不可用，顾问 web-search 回复待人工粘贴 brief。

---

## 2. 背景 Background（问题从何而来）

### 2.1 城市 pluvial flood 为什么难

短时强降雨可在数小时内淹没街道与低洼地。城市评估需要：(i) 可扩展的空间表示；(ii) 新观测到达时可更新；(iii) 评价时不因邻近样本泄漏而虚高分数。H3 提供嵌套六边形，便于多分辨率汇总与邻域查询。

### 2.2 对照文献（不是复制目标）

**Svellingen et al. (2026), *International Journal of Disaster Risk Reduction***（DOI: https://doi.org/10.1016/j.ijdrr.2026.106091）把机器学习得到的建筑级 **PFIb** 聚合到 H3，报告空间查询效率约提升 98%，并指出细（约 R13）与粗（约 R10）热点 Jaccard ≈ **0.14**。该文是 **H3 + pluvial** 最近的强对照，但它依赖专有/保险损害驱动的 PFIb，且主叙事是**聚合与沟通**，不是开放标签下的**空间诚实学习协议**。

本项目的问题 accordingly 改写为：

> 在**无法获取 PFIb** 的辖区，能否用开放多源标签在 H3 上完成：空间块评价、尺度损失诊断、由训练分驱动的自适应加密，并给出明确的非 PFIb 的 `PFI_h(c,r)` 定义？

### 2.3 写作架构（本报告与手稿共同遵守）

- **主结构：** IJDRR / 应用灾害风险期刊骨架（Intro → Related → Data → Methods → Results → Discussion → Conclusions）。  
- **主张纪律：** nature-writing / Nature claim discipline——证据 → 边界；动词用 *show / indicate / suggest*；禁止把 LM smoke 写成全市产品。  
- **文献顾问：** 目标会话 https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2 ；公开仓库 URL 索引：`artifacts/chatgpt_review_index.md`（raw.githubusercontent.com 供 ChatGPT 读取）。`cursor-ide-browser` 再次失败（`No browser tab available` / view 瞬时消失）；执行侧独立 WebSearch 继续成熟化手稿（含 Sun/Hu spatial CV 作者校正）与 `artifacts/literature_architecture_conclusions.md`。

---

## 3. 数据与方法 Data & Methods

### 3.1 研究区（必须反复强调边界）

配置中的 **Lower Manhattan bbox**（约 74.02–73.97°W，40.70–40.76°N；以 `configs/nyc.yaml` / `DOWNLOAD_MANIFEST.json` 为准）。这是 **Lower Manhattan Option B 试点范围**（n=262；遗留 smoke 141 仅 QA），**不是**纽约全市。

### 3.2 Live 图层（2026-08-15 工作区下载；非虚构）

| 图层 | 角色 |
|------|------|
| USGS 3DEP DEM 子集 | 高程 / 坡度等地形特征 |
| DEP stormwater flood polygons（Flooding_Category 1–2） | **模型导出**雨洪证据（非观测；category 3 海岸高潮位已剔除） |
| Building footprints | 建筑密度等 |
| USGS Ida high-water marks | 点状**观测**证据 |
| 311 street-flooding points（arcgis_streetfloodtime，2010–2014） | 点状开放证据（报告偏差风险；非 "2010–present"） |
| FEMA Sandy inundation | **仅负对照**，永不训练 |
| NLCD impervious | 不透水比例 |
| NHDPlus HR | `dist_stream_m` 作为 **distance-to-water** 代理（潮汐岸线语境下需谨慎解释） |
| FloodNet | 官方 `aq7i-eu5q`+`kb2e-tjy3` 已下载；**严格 held-out 诊断**（不入训练标签）；见 `outputs/floodnet_heldout_validation.json` |
| `event_rainfall.tif` | **合成常数** Ida-like 钩子，**不是** radar/gauge |

Provenance：`assembly_mode=opendata`；降雨侧仍可能报告 `rainfall_source=event_raster`。

### 3.3 H3 分辨率角色

| 用途 | 分辨率 | 说明 |
|------|--------|------|
| 训练主表 | R9 | `n_cells=262`（Option B） |
| Jaccard 细网格 | R10 | 热点分位 0.9 |
| Jaccard 父级 | R9 / R8 | mean / max / p90 上卷 |
| 自适应加密 | R11 | 高分父单元细化 |

### 3.4 模型与评价协议

- **主学习器：** 梯度提升分类器 + 证据分（evidence-score）回归器。  
- **基线：** L2 逻辑/线性，以及高程–不透水–坡度类规则（管道内；本报告以空间 CV 为主）。  
- **主指标：** spatial H3-block GroupKFold（5 folds，7 blocks）；**并报告类别占比与多数类平凡基线**（`outputs/classification_baselines.json`）。  
- **诊断：** random split val accuracy ≈ 0.759 —— **不得**在摘要中替代空间 CV。  
- **软件元数据：** h3 **4.4.2**（冻结产物 `models/nyc_smoke/run_metadata.json` / Option B `created_utc=2026-08-30` 记录值；仓库 pin `h3==4.4.2`；工作环境若见 4.5.0 属安装漂移，全量重跑前应重装 pin，勿把 metadata 改写成 live 版本）；sklearn 1.8.0；`random_seed=42`；framework `pluvial-flood-risk-dggs-h3` v0.1.0。

### 3.5 绑定定义：`PFI_h(c,r)`

\[
\mathrm{PFI}_h(c,r)=\widehat{P}(Y_c=1\mid X_c,r)
\]

静态特征 \(X_c\) 固定，降雨条件 \(r\) 在命名情景间变化。这是 **model output（模型输出）**，不是 SHAP/permutation importance，也不是 PFIb。当前 smoke 的情景表**尚未**显示非零响应（见 §5.6）。

#### 图 1 · `docs/paper/figures/workflow_schematic.png`

**来龙去脉：** 这是论文的 Figure 1 概念工作流图（SciencePlots + Times New Roman），由 `src/pluvial_flood_risk/figures.py` 的 `plot_workflow_schematic` 生成，无数据依赖，对应手稿 Methods 的四个阶段。  
**如何读：** 从左到右四列——(1) 开放多源输入（开放标签 + 静态特征 + 降雨条件 r）；(2) H3 组装（R9，带 provenance 标签）；(3) 学习与分块评价（梯度提升 + H3 块 GroupKFold 空间 CV + 常量类基线（恒判正/恒判负）+ 逻辑/积水规则基线）；(4) 诊断与输出（`PFI_h(c,r)`、Jaccard 尺度损失阶梯、自适应加密、Sandy 海岸淹没重叠诊断）。FEMA Sandy 是一条**虚线旁路**，绕过学习框、只进入 Sandy 诊断，绝非训练标签。  
**意义：** 一张图讲清整条协议与「证据—边界」纪律，帮助审稿人快速定位每一步对应的结果小节。  
**结论：** `PFI_h(c,r)` 是模型输出，不是特征重要性，也不是 PFIb；当前情景响应平坦（定义/接口已绑定，响应待观测降雨）；证据仅限两个 Manhattan 开放数据试点，非全市。

---

## 4. 过程 Process（怎么跑到这些图）

1. 下载/校验 `data/raw/nyc/`，写入 `DOWNLOAD_MANIFEST.json` / `DATA_SOURCES.md`。  
2. `build_nyc_h3.py --no-fixtures` → `data/processed/nyc_h3_cells.parquet`（opendata）。  
3. `pluvial-nyc-smoke` → `models/nyc_smoke/*`、`outputs/*`（空间 CV、Jaccard、自适应、情景、负对照）。  
4. SciencePlots + TNR 重绘六图到 `docs/paper/figures/`（工作流、空间结果图、源证据分解图、空间 CV、多分辨率空间图、分辨率效应；脚本 `scripts/make_figures.py`；另输出补充图 `supplementary/jaccard_by_resolution.png` 与 `supplementary/adaptive_ablation.png`）。  
5. `scripts/build_paper_report_html.py` → 自包含 `report.html`（Base64 图、内联 CSS）。  
6. Chrome headless `--print-to-pdf` → `report.pdf`（若失败，以 HTML 为准并记入 acceptance）。

**I2 阻塞说明：** 观测事件降雨 ingest 未完成；本报告**继续**基于 live outputs 写作，并在局限中诚实标注。

---

## 5. 结果 Results（只引用真实产物）

### 表 1 · 空间 CV 汇总（主分块评价表）

**来源：** `models/nyc_smoke/run_metadata.json`（模型折均）＋ `outputs/classification_baselines.json`（平凡基线，2026-08-17 固化）

| Metric | Value |
|--------|-------|
| n_cells | 262 |
| spatial_cv_n_folds / n_blocks | 5 / 12 |
| accuracy mean ± std | 0.808895 ± 0.045779 |
| F1 mean ± std | 0.846 |
| R² mean ± std | 0.227 ± 0.196 |
| MAE mean | 0.269818 |
| random_split_val_accuracy（诊断） | 0.792453 |
| 留出正类占比（prevalence） | 0.6298 |
| 多数类（恒判正）基线 accuracy | **0.629** |
| 多数类（恒判正）基线 F1 | **0.762** |
| 模型是否超过多数类基线 acc / f1 | **是 / 是** |
| 留出 ROC-AUC（pooled） | **0.847** |
| 留出 AP（pooled） | **0.851**（随机基线 = 正类占比 0.630） |

**来龙去脉：** smoke 跑完后，训练脚本把 GroupKFold 各折平均写入 metadata；随后 `scripts/compute_classification_baselines.py` 读取 `spatial_cv_folds.csv`，对每折计算“全部判正”“全部判负”两种平凡基线并写入 `outputs/`。这是论文/报告里**唯一优先引用的评价汇总**，且**必须**连同类别占比与多数类基线一起引用。**历史注记（pre-Option-B，n=141）：** 2026-08-23 C1/C5/M5 与 2026-08-24 M4 曾把 smoke 表正类从 80.1%→69.5%→67.4%、并更新 ROC-AUC/accuracy/F1。**当前真相是 Option B n=262（正类 63.7%，acc 0.820，F1 0.858，ROC-AUC 0.848；扩展 n=956 正类 47.9%，acc 0.823，F1 0.826，ROC-AUC 0.882；见 outputs/paper_results.json），勿把上述 n=141 数字当作现行主表。**SLR 敏感性（`outputs/slr_sensitivity.json`，post–76ig-c548 重跑）：** LM n=262 正类 167→177（63.7%→67.6%）、pooled ROC-AUC 0.848→0.836；扩展窗口 458→478（47.9%→50.0%）、pooled ROC-AUC 0.882→0.872。两情景下实质结论不变。（历史注记 pre-Option-B n=141：曾报告 67.4%→69.5%、ROC-AUC 0.780→0.741。）**  
**如何读：** 先看正类占比（0.637，即 63.7% 留出单元为正），再看多数类基线（恒判正 acc 0.637 / F1 0.769），最后才看模型分数（0.820 / 0.858）。模型分数**超过**多数类基线（0.820 > 0.637；0.858 > 0.769）；留出 ROC-AUC 0.848、AP 0.855 高于 0.637 随机基线，支持**中等偏强排序判别力**。证据分 R² 为 0.191 ± 0.287，解释力有限。随机划分准确率仅作诊断，不能当主结果。  
**意义：** 空间块留出让评价设计更诚实；在类别失衡时，accuracy/F1 必须与平凡基线对照。修订后的模型在小窗口已能超过多数类基线，但这是**单一小试点**的结果，不得外推到全市。  
**结论（允许）：** LM smoke 上协议可跑通（能训练、能分块评价、能出表），模型在小窗口超过多数类平凡基线。  
**结论（禁止）：** 全市技能；“强分类判别力”（阈值化 accuracy/F1 虽超过多数类基线，但 ROC-AUC/AP 仅为中等，且 n=262 仍为亚城市试点）；用随机划分替换空间 CV；“已解决事件响应预报”。

### 表 2 · 逐折明细

**来源：** `models/nyc_smoke/spatial_cv_folds.csv`

| fold | n_train | n_test | accuracy | f1 | r2 | mae |
|------|---------|--------|----------|-----|-----|-----|
| 0 | 209 | 53 | 0.755 | 0.831 | +0.216 | 0.294 |
| 1 | 209 | 53 | 0.887 | 0.938 | -0.138 | 0.276 |
| 2 | 211 | 51 | 0.784 | 0.807 | +0.403 | 0.262 |
| 3 | 209 | 53 | 0.830 | 0.836 | +0.390 | 0.247 |
| 4 | 210 | 52 | 0.788 | 0.820 | +0.267 | 0.271 |

**来龙去脉：** 每个 fold 留出 1–2 个粗 H3 父块；测试块 ID 列在 CSV 的 `test_block_ids`。  
**如何读：** 折间 accuracy/F1 仍有跳动（块大小与正负类比例不均）——这正是必须同时报告 **std** 的原因。  
**意义：** 展示评价协议的折间不稳定性，而不是“挑最好一折”。  
**结论：** 均值有效，但外部效度仍受小样本与块不均限制。

#### 图 2 · `docs/paper/figures/spatial_maps.png`

**来源：** `data/processed/nyc_h3_cells.parquet`（flood_evidence_score / `flood_risk` 列）＋ `models/nyc_smoke/spatial_cv_oof_predictions.csv`（留出分数）＋ `outputs/pfi_h_scenarios.parquet`（PFI_h，ida_like 情景）＋ `data/raw/nyc/dem.tif`（地形底图）＋ `data/raw/nyc/hydro_streams.geojson`（岸线水系统）。

**来龙去脉：** 这是对照参考论文（Svellingen et al. 2026 IJDRR）"结果先行出空间图"体例新增的**直观结果图**。用 `h3.cell_to_boundary` 生成 262 个 R9 六边形面片，三面板同支撑：**(a)** 开放证据分 `flood_evidence_score`（双峰构造：无证据=0、任一证据=高值，中位数 1.0、均值 0.598，≥0.8 共 84 格）；**(b)** H3 块空间 CV 的留出分数（均值 0.655）；**(c)** 全拟合模型分 `PFI_h(c,r)`（合成 ida_like 情景 r=75 mm/h，均值 0.630；**deployment_full 全拟合输出，非留出验证图**）。底图为 DEM 灰阶地形 + NHDPlus 岸线水系（浅蓝）。

**如何读：** 三面板同色标 0–1。(a) 呈强二元对比；(b)(c) 分数平滑。观测~留出 Pearson r=0.467，观测~PFI_h r=0.765，留出~PFI_h r=0.634——与 §5.1 的"排序判别中等"叙事一致：模型表面在 63.0% 正类的 Option B 窗口下仍偏乐观，不构成强判别证据。

**意义：** 提供论文首个直观空间结果（评审"先直观后统计"要求）；同时诚实展示"标签双峰分布→概率连续平滑"的差距。

**结论（允许）：** 图面仅作视觉检视；三面板同源同支撑，数字与 §5.1/§5.6 完全一致。  
**结论（禁止）：** 把图面高低当作独立验证；从 r=0.401 读出"模型失效"或"模型完美"（label 双峰构造是 r 偏低的主因之一）；把全拟合 panel (c) 当作第三种验证结果。

#### 图 3 · `docs/paper/figures/source_evidence_maps.png`

**来源：** `data/processed/nyc_h3_cells.parquet` 的源区分列（`dep_area_frac` / `complaint_count` / `ida_hwm_count` / `flood_risk`）＋ `data/raw/nyc/dem.tif`（地形底图）＋ `data/raw/nyc/hydro_streams.geojson`（岸线水系）。

**来龙去脉：** 这是 2026-08-23 审稿修订（C3：源区分 provenance）新增的**直观源证据分解图**，把「三源被保留为独立列、再合成 composite」这件事从代码列存在变成可视可读。四面板同 R9 支撑：**(a)** DEP 雨水洪泛多边形面积分数（category 1–2，连续 0–1 viridis）；**(b)** 311 众包报告计数（magma 计数色标）；**(c)** USGS Ida 高水位点计数（plasma 计数色标）；**(d)** composite `flood_risk` 证据分（viridis 0–1）。图 2(a) 的 composite 表面在此被拆成「哪个源驱动了每个高证据单元」。

**如何读：** (a)(d) 共享 0–1 连续色标；(b)(c) 用计数色标。看三源的单元集**重叠但不完全相同**，而 (d) 是三者取 max 的结果——这正是 Highlights 声称「three sources are kept distinct」的可视化证据。

**意义：** 直接回应审稿人对「source kept distinct 只是文档措辞、训练表未保留源列」的质疑；同时满足「增加直观空间图、减少单调统计图」的要求。

**结论（允许）：** DEP/311/HWM 三源在 H3 支撑上空间部分重叠但不重合；composite = 三者 max，非无差别合并。  
**结论（禁止）：** 把 DEP 面板当作独立「观测洪水」；把计数色标（b/c）与 0–1 连续色标（a/d）混读。

#### 图 4 · `docs/paper/figures/spatial_cv_folds.png`

**来龙去脉：** 由 `spatial_cv_folds.csv` 经 `src/pluvial_flood_risk/figures.py`（SciencePlots + TNR）绘制 Accuracy/F1 成对标记点，末位为 Mean±SD 误差棒；三条水平参考线分别标注恒判正 accuracy、恒判正 F1、恒判负 accuracy。  
**如何读：** 横轴 fold_id + Mean±SD；纵轴 0–1；每折两个偏移标记点（圆=Accuracy、方=F1）。  
**意义：** 把表 2 变成可一眼比较的稳定性图。  
**结论：** 五折 Accuracy≈0.75–0.89，F1≈0.81–0.94；与表 1 一致。仍是 LM Option B（n=262）。

---

### 表 3 · Jaccard 尺度损失阶梯

**来源：** `outputs/jaccard_by_resolution.csv`（fine_res=10，strict 10% area budget; fractional ties）

| coarse | agg | jaccard | f1 | fine-parent recall | coarse precision |
|--------|-----|---------|-----|-------------------|------------------|
| 8 | max | 0.570 | 0.726 | 0.726 | 0.726 |
| 8 | mean | 0.136 | 0.239 | 0.239 | 0.239 |
| 8 | p90 | 0.682 | 0.811 | 0.811 | 0.811 |
| 9 | max | 0.649 | 0.787 | 0.787 | 0.787 |
| 9 | mean | 0.227 | 0.370 | 0.370 | 0.370 |
| 9 | p90 | 0.571 | 0.727 | 0.727 | 0.727 |
