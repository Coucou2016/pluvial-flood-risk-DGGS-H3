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
| LM smoke（Lower Manhattan smoke） | 下曼哈顿包围盒上的开放数据烟雾测试（`n_cells=141`），**≠ citywide** |
| assembly_mode=opendata | 训练表由观测开放图层组装（非 fixture 合成表） |
| fixture / synthetic demo | 管道 QA 用合成数据；**≠ science** |
| I2（观测事件降雨） | 计划接入 gauge/radar 事件降雨；当前仍阻塞，仅有合成常数 `event_raster` |
| Negative control（负对照） | FEMA Sandy 沿海淹没叠置检查；**永不作为训练标签** |
| SciencePlots | matplotlib 学术样式插件；本报告图使用 Times New Roman（TNR） |
| Trivial / constant baseline（平凡基线 / 常量基线） | 不做学习的“闭眼”预测（如恒判正类 always-positive、恒判负类 always-negative）；用于对照模型是否真的学到判别力；真多数类由 pooled 类别数推导 |

---

## 1. 摘要 Abstract

本报告是仓库 **live Lower Manhattan open-data smoke** 的教师向（teacher-like）过程说明：不只贴图，而是交代每张表/图的**来龙去脉、如何读、意义、可下的结论、不可下的结论**。

在 H3 分辨率 R9 上组装 **n_cells = 141** 个六边形单元，`assembly_mode=opendata`。主（**分块评价**）指标为 **spatial H3-block CV（空间 H3 块交叉验证）**：准确率均值 **0.808090 ± 0.085380**，F1 均值 **0.863716 ± 0.0612**（来源：`models/nyc_smoke/run_metadata.json`，`created_utc=2026-08-23T14:42:55Z`）。**关键修订（2026-08-23，C1 修复后）：** 留出样本正类占比 **69.5%**（剔除 DEP category 3 海岸高潮位后），恒判正的多数类平凡基线在同样折上可达 accuracy **0.687**、F1 **0.813**，此时模型 **0.808 / 0.864 已超过**该平凡基线——这是本轮审稿修订（C1）带来的实质结论变化（来源：`outputs/classification_baselines.json`）。尺度损失用开放证据 **Jaccard ladder** 诊断：细 R10→粗 R9 **mean** 聚合 Jaccard = **0.210**、细 R10→粗 R8 **mean** 聚合 Jaccard = **0.167**（R10 为原生 overlay，无 parent inheritance；不得写成“复现了 Svellingen 的 0.14”）。自适应相对均匀细网格（R11）单元数比 **adaptive_cell_count_ratio ≈ 0.604**。

**诚实缺口（待补充）：** (1) I2 观测事件降雨仍阻塞，`rainfall_source=event_raster` 为合成常数钩子；(2) `outputs/pfi_h_scenarios.parquet` 四情景（25/40/75/100 mm/h）下，**单元内 PFI_h 极差 = 0**，情景均值同为 ≈0.6908，故**不宣称**已观察到降雨条件判别力；(3) LM ≠ citywide；(4) ChatGPT 浏览器 MCP 本会话不可用，顾问 web-search 回复待人工粘贴 brief。

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

配置中的 **Lower Manhattan bbox**（约 74.02–73.97°W，40.70–40.76°N；以 `configs/nyc.yaml` / `DOWNLOAD_MANIFEST.json` 为准）。这是 **pilot smoke extent**，**不是**纽约全市。

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
| FloodNet | 默认关闭 / 未接入；opt-in |
| `event_rainfall.tif` | **合成常数** Ida-like 钩子，**不是** radar/gauge |

Provenance：`assembly_mode=opendata`；降雨侧仍可能报告 `rainfall_source=event_raster`。

### 3.3 H3 分辨率角色

| 用途 | 分辨率 | 说明 |
|------|--------|------|
| 训练主表 | R9 | `n_cells=141` |
| Jaccard 细网格 | R10 | 热点分位 0.9 |
| Jaccard 父级 | R9 / R8 | mean / max / p90 上卷 |
| 自适应加密 | R11 | 高分父单元细化 |

### 3.4 模型与评价协议

- **主学习器：** 梯度提升分类器 + 证据分（evidence-score）回归器。  
- **基线：** L2 逻辑/线性，以及高程–不透水–坡度类规则（管道内；本报告以空间 CV 为主）。  
- **主指标：** spatial H3-block GroupKFold（5 folds，7 blocks）；**并报告类别占比与多数类平凡基线**（`outputs/classification_baselines.json`）。  
- **诊断：** random split val accuracy ≈ 0.690 —— **不得**在摘要中替代空间 CV。  
- **软件元数据：** h3 4.4.2；sklearn 1.8.0；`random_seed=42`；framework `pluvial-flood-risk-dggs-h3` v0.1.0。

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
| n_cells | 141 |
| spatial_cv_n_folds / n_blocks | 5 / 7 |
| accuracy mean ± std | 0.808090 ± 0.085380 |
| F1 mean ± std | 0.863716 ± 0.0612 |
| R² mean ± std | 0.078968 ± 0.338043 |
| MAE mean | 0.326358 |
| random_split_val_accuracy（诊断） | 0.620690 |
| 留出正类占比（prevalence） | 0.6950 |
| 多数类（恒判正）基线 accuracy | **0.687** |
| 多数类（恒判正）基线 F1 | **0.813** |
| 模型是否超过多数类基线 acc / f1 | **是 / 是** |
| 留出 ROC-AUC（pooled） | **0.741** |
| 留出 AP（pooled） | **0.803**（随机基线 = 正类占比 0.695） |

**来龙去脉：** smoke 跑完后，训练脚本把 GroupKFold 各折平均写入 metadata；随后 `scripts/compute_classification_baselines.py` 读取 `spatial_cv_folds.csv`，对每折计算“全部判正”“全部判负”两种平凡基线并写入 `outputs/`。这是论文/报告里**唯一优先引用的评价汇总**，且**必须**连同类别占比与多数类基线一起引用。**注意：2026-08-23 审稿修订（C1：剔除 DEP category 3 海岸高潮位、C5：负对照分组修复、M5：ponding 基线去泄漏）后，正类占比从 80.1% 降至 69.5%，模型 accuracy/F1 从“低于多数类基线”变为“超过多数类基线”。**  
**如何读：** 先看正类占比（0.695，即 69.5% 留出单元为正），再看多数类基线（恒判正 acc 0.687 / F1 0.813），最后才看模型分数（0.808 / 0.864）。模型分数**超过**多数类基线（0.808 > 0.687；0.864 > 0.813），说明在空间块留出下模型具备超过“闭眼判洪”的判别力；留出 ROC-AUC 0.741、AP 0.803 高于 0.695 随机基线，进一步支持**中等排序判别力**。但 R² 仍接近 0（0.079），说明证据分回归对“人造 evidence score”的解释力有限。随机划分准确率（0.621）低于空间 CV，仅提示“换协议分数会变”，不能当主结果。  
**意义：** 空间块留出让评价设计更诚实；在类别失衡时，accuracy/F1 必须与平凡基线对照。修订后的模型在小窗口已能超过多数类基线，但这是**单一小试点**的结果，不得外推到全市。  
**结论（允许）：** LM smoke 上协议可跑通（能训练、能分块评价、能出表），模型在小窗口超过多数类平凡基线。  
**结论（禁止）：** 全市技能；“强分类判别力”（阈值化 accuracy/F1 虽超过多数类基线，但 ROC-AUC/AP 仅为中等，且 n=141 小样本）；用随机划分替换空间 CV；“已解决事件响应预报”。

### 表 2 · 逐折明细

**来源：** `models/nyc_smoke/spatial_cv_folds.csv`

| fold | n_train | n_test | accuracy | f1 | r2 | mae |
|------|---------|--------|----------|-----|-----|-----|
| 0 | 92 | 49 | 0.755 | 0.842 | −0.362 | 0.402 |
| 1 | 116 | 25 | 0.840 | 0.882 | −0.037 | 0.370 |
| 2 | 119 | 22 | 0.773 | 0.839 | −0.048 | 0.365 |
| 3 | 120 | 21 | 0.714 | 0.786 | 0.183 | 0.301 |
| 4 | 117 | 24 | 0.958 | 0.970 | 0.659 | 0.194 |

**来龙去脉：** 每个 fold 留出 1–2 个粗 H3 父块；测试块 ID 列在 CSV 的 `test_block_ids`。  
**如何读：** Fold4 准确率 0.917 明显高于其他折——这正是必须同时报告 **std** 的原因：块大小与正负类比例不均时，单折会跳动。  
**意义：** 展示评价协议的折间不稳定性，而不是“挑最好一折”。  
**结论：** 均值有效，但外部效度仍受小样本与块不均限制。

#### 图 2 · `docs/paper/figures/spatial_maps.png`

**来源：** `data/processed/nyc_h3_cells.parquet`（flood_evidence_score / `flood_risk` 列）＋ `models/nyc_smoke/spatial_cv_oof_predictions.csv`（留出分数）＋ `outputs/pfi_h_scenarios.parquet`（PFI_h，ida_like 情景）＋ `data/raw/nyc/dem.tif`（地形底图）＋ `data/raw/nyc/hydro_streams.geojson`（岸线水系统）。

**来龙去脉：** 这是对照参考论文（Svellingen et al. 2026 IJDRR）"结果先行出空间图"体例新增的**直观结果图**。用 `h3.cell_to_boundary` 生成 141 个 R9 六边形面片，三面板同支撑：**(a)** 开放证据分 `flood_evidence_score`（双峰构造：无证据=0、任一证据=高值，中位数 1.0、均值 0.600，≥0.8 共 84 格）；**(b)** H3 块空间 CV 的留出分数（均值 0.692）；**(c)** 全拟合模型分 `PFI_h(c,r)`（合成 ida_like 情景 r=75 mm/h，均值 0.691；**全拟合模型输出，非留出验证图**）。底图为 DEM 灰阶地形 + NHDPlus 岸线水系（浅蓝）。

**如何读：** 三面板同色标 0–1。(a) 呈强二元对比；(b)(c) 分数平滑。观测~留出 Pearson r=0.401，观测~PFI_h r=0.703，留出~PFI_h r=0.617——与 §5.1 的"排序判别中等"叙事一致：模型表面在 69.5% 正类的极小窗口下仍偏乐观，不构成强判别证据。

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
**结论：** 多数折 Accuracy≈0.71–0.84，Fold4（n=24）抬高均值至 0.958；与表 1 一致。仍是 LM smoke。

---

### 表 3 · Jaccard 尺度损失阶梯

**来源：** `outputs/jaccard_by_resolution.csv`（fine_res=10，hotspot_quantile=0.9）

| coarse | agg | jaccard | f1 |
|--------|-----|---------|-----|
| 8 | mean | 0.1667 | 0.2857 |
| 8 | max | 1.0000 | 1.0000 |
| 8 | p90 | 0.5000 | 0.6667 |
| 9 | mean | 0.2099 | 0.3469 |
| 9 | max | 1.0000 | 1.0000 |
| 9 | p90 | 0.5432 | 0.7040 |

附：细网格 n_fine=991，热点 n_hotspot_fine=149（阈值；**原生 overlay，无 parent inheritance**）。

**来龙去脉：** 在细 R10 上**直接把原始 polygon/point 几何 overlay 到原生 R10**，取高分热点集合，再按父单元用 mean/max/p90 聚合后与粗网格热点比 Jaccard/F1。目的是诊断 **MAUP / scale-loss**，不是复现 PFIb 文献数字。**注意：2026-08-23 审稿修订（C3）删除了旧版 "R9 polygon 分继承到 R10 children" 的循环路径，R10 热点从旧 571/991（57.6%，因分数饱和）变为 149/991（15.0%），R10→R9 mean Jaccard 从 0.977 降至 0.210，真实揭示尺度损失。**  
**如何读：** 关注 **mean@R8=0.167、mean@R9=0.210**：mean 聚合大幅抹平细热点；max/p90 接近/等于 1 是因为极值保留机制，**不是**“粗网格完美”。  
**意义：** 说明“沟通用粗网格”与“安全关键细热点”不可混为一谈——这与 Svellingen 的尺度权衡叙事**概念对话**，但标签栈不同。  
**结论（允许）：** 开放证据下，mean 上卷到 R9/R8 会严重改变热点集合（Jaccard 0.21/0.17）。  
**结论（禁止）：** “我们得到了与 Svellingen 相同的 Jaccard 0.14”；把 max/p90=1 写成模型完美。

#### 图 5 · `docs/paper/figures/multi_resolution_spatial.png`

**来源：** `data/processed/nyc_h3_cells_r10_labels.parquet`（991 个 R10 单元）经 `h3.cell_to_parent` mean 上卷至 R9（160）/ R8（31），与图 6 完全同源。

**来龙去脉：** 对照参考论文 Fig 4 体例新增的"多分辨率空间并排图"。(a) R10 开放标签分（n=991）；(b) R9 mean 上卷（n=160）；(c) R8 mean 上卷（n=31）。三面板同一地理足迹、共享 0–1 viridis 色标，把"粗化伴随的平滑"直接变成可视的空间压缩，不新增任何统计量。

**如何读：** 三面板从细到粗，看细粒度热点在 R9/R8 均值上卷后如何被抹平；颜色只表达开放标签分（0–1），与图 6 的分布压缩互补。

**意义：** 补齐参考论文最重要的"多分辨率空间图"图型，与图 6（统计视图）构成"空间效应 + 统计效应"双层证据。

**结论（允许）：** 开放标签分在 R10 呈现局部热点，mean 上卷到 R8 后热点被平滑。  
**结论（禁止）：** 把面板颜色深浅当作独立验证；声称该图证明"模型准确"。

#### 补充图 S1 · `docs/paper/figures/supplementary/jaccard_by_resolution.png`

**来龙去脉：** 表 3（Jaccard 阶梯）的偏移标记散点（左 Jaccard similarity、右 F1；标记形状/颜色区分 mean/max/p90，共享图例），与表 3 同 CSV。原为主文图 4，W9 按"多分辨率空间图优先"调整为补充材料。  
**如何读：** 随 coarse_res 变粗，看 mean 标记在 R8 是否明显下降；max/p90 接近 1 是极值保留机制。  
**意义：** 可视化尺度损失（数值已完整列于表 3）。  
**结论：** mean 在 R8 损失最大；禁止与 PFIb 的 0.14 数值等同。

#### 图 6 · `docs/paper/figures/resolution_effects.png`

**来源：** `data/processed/nyc_h3_cells_r10_labels.parquet`（991 个 R10 单元）经 `h3.cell_to_parent` mean 上卷至 R9（160）/ R8（31）。

**来龙去脉：** 对照参考论文 Fig 5 体例新增的分辨率效应双面板图。(a) **小提琴分布**：R10/R9/R8 三个分辨率上开放证据分的分布（叠加原始点），展示聚合对分布的压缩（R10 宽而双峰→R8 窄带）。所有分位/上卷与 `outputs/jaccard_by_resolution.csv` 同源（q=0.9、mean/max/p90），数值经脚本核对一致。(b) **跨分辨率 Jaccard 相似度热力矩阵**：R10/R9/R8 三分辨率热点集合两两 Jaccard（每对在较粗支撑上计算），对角为 1，R10-vs-R9=0.210、R10-vs-R8=0.167 与表 3（Jaccard 阶梯 mean 行）完全一致；新增 R9-vs-R8=0.167。两个 R8 相关项同为 0.167 是实际数据结果，不是方法强制（实证）。

**如何读：** (a) 看三条分布由宽变窄的压缩过程（叠加点可确认 R8 n=31 的真实散布）；(b) 看非对角项沿远离对角线方向衰减：0.210→0.167 说明跨分辨率热点相似度本已不高，随进一步粗化继续下降。

**意义：** 把"尺度损失"从一张阶梯表变成"分布压缩 + 集合持久性"两张互补的统计视图，直接对齐参考论文的类型覆盖。

**结论（允许）：** 与表 3 数值一致；开放证据下粗化会同时压缩分布并降低跨分辨率热点相似度。  
**结论（禁止）：** 把矩阵中的 0.210/0.167 与 Svellingen 的 PFIb Jaccard 0.14 做数值等同；把 max/p90=1 解释为"粗网格无损失"。

---

### 表 4 · 自适应 vs 固定 / 均匀细网格

**来源：** `outputs/adaptive_vs_fixed_ablation.csv`

| Field | Value |
|-------|-------|
| score_col | PFI_h |
| n_fixed_coarse (R9) | 141 |
| n_adaptive_mixed | 4173 |
| n_uniform_fine (R11) | 6909 |
| adaptive_cell_count_ratio (adaptive/uniform) | 0.603995 |
| parents_refined | 84 |
| score_quantile | 0.8 |
| coarse→fine | 9→11 |

**来龙去脉：** 训练后用 `PFI_h`（全拟合/in-sample 分数）筛高分父单元，再加密到 R11，形成混合分辨率网格；与“全部留在 R9”和“全部升到 R11”对比单元数。**注意：2026-08-23 审稿修订（M3）后，本表定位为“表征规模（representation-size）比较”，不再主张“效率提升/hotspot retention”，因为选择用 in-sample 分数、uniform R11 仅为 child-count 估算、未重训 R11。**  
**如何读：** 141 → 4173 → 6909；自适应 = 29.6× 固定 R9 = 60.4% 均匀 R11（比率 0.604）。  
**意义：** 在计算预算与局部细化之间的工程折中；分数来源写明为 trained PFI_h（in-sample）。  
**结论（允许）：** 本 smoke 设定下自适应把均匀细网格单元数降到约六成（**仅单元数**）。  
**结论（禁止）：** 全市算力节省；自适应已提高泛化技能（本表是**单元数**消融，不是技能提升表，也不是 runtime/memory/hotspot 证据）。

#### 补充图 S2 · `docs/paper/figures/supplementary/adaptive_ablation.png`

**来龙去脉：** 三柱条形图对应表 4 三个单元数，顶部标注「Adaptive = 29.6× fixed R9 = 60.4% of uniform R11（representation size only）」。2026-08-23 审稿修订（M5）将其**从主图降级为补充图**：这是单元数（representation-size）比较，数值已列于正文 Table 5，单调粗三柱图没有必要占据主文图位。  
**如何读：** 中间柱应介于左右之间；顶部标注直接给出两个比率。  
**意义：** 仅作表 4/Table 5 的可视化补充。  
**结论：** 与表 4 一致；非全市声明。

---

### 表 5 · Sandy 负对照

**来源：** `outputs/negative_control.json`

| Field | Value |
|-------|-------|
| n_cells | 141 |
| n_coastal / n_pluvial / n_both | 31 / 98 / 22 |
| n_coastal_only / n_pluvial_only | 9 / 76 |
| n_neither | 34 |
| frac_coastal_only | 0.0638 |
| score_col | **oof_model_score**（留出模型分，非 target） |
| mean_score_coastal_only | 0.644 |
| mean_score_pluvial_only | 0.840 |
| mean_score_both | 0.771 |
| mean_score_neither | 0.323 |
| pluvial_minus_coastal_mean_score | **0.195** |
| coastal_only_among_high_score | 0.034 |
| pluvial_among_high_score | 0.759 |
| assembly_mode | opendata |

**来龙去脉：** 把 FEMA Sandy 沿海淹没与开放 pluvial 证据叠在同一批 H3 单元上，检查空间是否完全重合。**注意：2026-08-23 审稿修订（C4）后，负对照的 score 比较从 target `flood_risk` 改为留出（OOF）模型分 `oof_model_score`**——因为 coastal-only 单元 `flood_class=0` 是定义，其 target `flood_risk=0` 是恒等式，用 target 比较是循环论证；只有 OOF 模型分才能检验「模型是否把证据集中到纯海岸单元」。同时 pluvial 分组沿用 composite `flood_class==1`（含点标签），修复旧版 `flood_area_frac>0` 的 "neither" 行异常。

**如何读：** `n_coastal_only=9`（6.4%）的**留出模型分均值为 0.644**，并非 0——说明模型确实**部分学习了低海拔/近岸信号**；`n_pluvial_only=76` 的留出分为 0.840，分差 0.195。因此模型并非「完全不把证据集中在海岸单元」，但 pluvial-only 仍最高、top-20% 分数单元中 coastal-only 仅占 3.4%，说明模型没有被海岸位置单独驱动。这是比旧版（coastal-only target=0.000、分差 0.888）**更诚实**的结论。

**意义：** 负对照真正回答了「模型是否偷学海岸位置」：答案是「部分（coastal-only OOF=0.644 vs neither=0.323），但不主导（pluvial-only=0.840 更高，top 分数单元 75.9% 为 pluvial）」。

**结论（允许）：** 证据空间不完全重合；留出模型分在 coastal-only 单元非零，提示海岸混杂在特征层面部分存在；但 pluvial 信号仍占主导。  
**结论（禁止）：** 不得声称「已用 target 证明海岸混杂被消除」（那会是循环论证）；不得将 Sandy 用作训练标签。

---

### 5.6 PFI_h 降雨情景（诚实缺口 · 待补充）

**来源：** `outputs/pfi_h_scenarios.csv`（564 行 = 141 单元 × 4 情景）

| scenario | rainfall_mm_h | mean PFI_h |
|----------|---------------|------------|
| moderate | 25 | 0.6908 |
| heavy | 40 | 0.6908 |
| Ida-like | 75 | 0.6908 |
| extreme | 100 | 0.6908 |

**核验：** 按 `h3_index` 分组，`max(PFI_h)-min(PFI_h)` 的全局最大值为 **0.0**。  
**来龙去脉（根因已确诊，2026-08-17）：** 情景循环本身正确——只改 `rainfall_mm_h` 再预测，产物里 4 个情景的 `rainfall_mm_h` 也确实分别是 25/40/75/100。平坦的真正原因是**训练阶段降雨是常数**：训练表 `data/processed/nyc_h3_cells.parquet` 的 141 个单元 `rainfall_mm_h` 全部为 **75.0**（`rainfall_source=event_raster` 的合成常数钩子），因此 `rainfall_mm_h` 在训练特征矩阵中方差为 0；`GradientBoostingClassifier` 对该列的特征重要性为 **0.0**（`models/nyc_smoke/classifier.joblib`）。模型从未见过降雨变化，自然无法对情景做出响应。  
**结论：** **定义保留**；**经验判别力本轮不成立**，且成因不是 bug 而是“训练降雨恒为常数”。要得到非零响应，必须先引入 I2 观测事件降雨（多强度、非合成 provenance），再重训；在此之前禁止在摘要写“情景响应已验证”。

### 5.7 扩展 bbox 主表（`manhattan_expanded`，`n=956`）

**来源：** `outputs/expanded_primary_table.json`、`models/nyc_expanded/spatial_cv_folds.csv`、`outputs/classification_baselines_expanded.{json,csv}`；原始数据在 `data/raw/nyc_expanded/`（`DOWNLOAD_MANIFEST.json` 可溯源）。

**来龙去脉：** §5.1 的 `n=141` 表只覆盖 Lower Manhattan 极小窗口。为检验模型表现是否只是“极小 bbox 落在 DEP 洪泛多边形内”造成的**范围敏感现象（extent-sensitivity 假设）**，本小节把同样的开放数据协议跑在更大的 `manhattan_expanded` 范围（`[-74.03, 40.68, -73.94, 40.80]`，约 0.09° × 0.12°，从曼哈顿下城向上城/中城南扩展），得到 `n=956` 个 R9 单元、28 个空间块。注意：这一步只“扩大范围再跑一次”，**不构成**对“小窗口范围敏感”的证明——除非后续量化两个范围下各标签分量（DEP/311/Ida）的覆盖差异。**注意：2026-08-23 审稿修订（C1：剔除 DEP category 3）后两个窗口数字均变化，本表为修订后值。**

**如何读：** 下表与 §5.1 表 1 同构，便于直接对照“小窗口 vs 扩展窗口”。

| Metric | 扩展窗口 (`manhattan_expanded`) | 小窗口 (LM smoke) |
|--------|-------------------------------|-------------------|
| n_cells | **956** | 141 |
| spatial_cv_n_blocks | **28** | 7 |
| spatial_cv_n_folds | 5 | 5 |
| 正类占比（held-out） | **0.497** | 0.695 |
| spatial_cv_accuracy_mean ± std | **0.824 ± 0.013** | 0.808 ± 0.085 |
| spatial_cv_f1_mean | **0.832** | 0.864 |
| spatial_cv_r2_mean ± std | **0.346 ± 0.138** | 0.079 ± 0.338 |
| spatial_cv_mae_mean | **0.284** | 0.326 |
| random_split_val_accuracy（仅诊断） | 0.844 | 0.621 |
| always-positive accuracy | **0.497** | 0.687 |
| always-positive F1（折内均值） | **0.663** | 0.813 |
| always-negative accuracy | **0.503** | 0.313 |
| always-negative F1（正类） | 0.000 | 0.000 |
| 恒定多数类（真多数类） | 恒判负，acc 0.503 | 恒判正，acc 0.687 |
| 模型是否超过恒定多数类 accuracy | **是（0.824 > 0.503）** | 是（0.808 > 0.687） |
| 模型是否超过 always-positive F1 | **是（0.832 > 0.663）** | 是（0.864 > 0.813） |
| ROC-AUC（pooled，留出） | **0.875** | 0.741 |
| AP / average precision（pooled，留出） | **0.822** | 0.803 |
| 随机 AP 基线（=正类占比） | 0.497 | 0.695 |

**逐折明细（`models/nyc_expanded/spatial_cv_folds.csv`）：**

| fold | n_test | 正/负 | accuracy | f1 | r2 |
|------|--------|-------|----------|----|----|
| 0 | 191 | 108 / 83 | 0.827 | 0.845 | 0.445 |
| 1 | 191 | 97 / 94 | 0.848 | 0.857 | 0.385 |
| 2 | 191 | 98 / 93 | 0.817 | 0.837 | 0.273 |
| 3 | 190 | 82 / 108 | 0.821 | 0.805 | 0.508 |
| 4 | 193 | 90 / 103 | 0.808 | 0.816 | 0.118 |

**意义（为什么这个表重要）：**

1. **类别失衡随空间范围变化。** 扩展窗口正类占比 49.7%（正 475 / 负 481，近均衡），小窗口 69.5%（多数类为正）。这提示两个范围的正类覆盖差异较大（范围敏感），但本报告**尚未量化**两个范围下各标签分量（DEP/311/Ida）的覆盖差异，因此不宣称“已证明”范围敏感的具体成因。**注意：2026-08-23 修复扩展窗口数据路径 bug（此前误用 `data/raw/nyc/` 下的小窗口栅格/311 快照覆盖在扩展 bbox 上）后，扩展窗口正类占比由 36.5% 升至 49.7%（311 证据单元由 145→367），各项指标相应更新。**
2. **两个窗口 accuracy 都超过各自恒定多数类基线。** 小窗口 0.808 > 0.687（恒判正）、扩展窗口 0.824 > 0.503（恒判负）。这是阈值化 accuracy 层面的证据，但**不等同于**阈值无关的判别力证明。
3. **证据分 R² 随范围变化。** 小窗口 R²≈0.079，扩展窗口 R²≈0.346，说明在更大样本上证据分回归出现正信号。但单个扩展试点**不能**归因于“样本规模不足是小窗口 R² 近零的原因”——该差异只表明范围敏感，未识别其具体成因。
4. **扩展窗口 F1 已超过 always-positive 比较器（0.832 > 0.663，折内均值），且逐折 F1 稳定（0.805–0.857）。** 修复数据路径 bug 后，扩展窗口的逐折类别构成近均衡（正类测试数 82–108），F1 不再出现旧版 Fold3=0.167 的极端波动。小窗口 F1 亦超过 always-positive（0.864 > 0.813）。
5. **阈值无关判别指标为中等偏强。** 留出 pooled ROC-AUC：小窗口 0.741、扩展窗口 0.875；AP：小窗口 0.803（基线 0.695）、扩展窗口 0.822（基线 0.497），均明显高于各自随机基线。但 ROC-AUC/AP 只回答“排序是否优于随机”，不回答“正类 F1 是否优于 always-positive”；结合第 4 点，两个窗口的 F1 均已超过各自平凡比较器，故总体结论上调为**判别力中等偏强（仍非“强分类技能”，且非全市）**。

**结论（honest）：** 扩展窗口主表**不是全市结果**（仍是曼哈顿试点），但两个窗口在空间块留出下都建立了**超过各自多数类基线的阈值化 accuracy 与超过 always-positive 比较器的 F1**，且留出 ROC-AUC（0.741 / 0.875）与 AP（0.803 / 0.822）均高于各自随机基线，给出**中等偏强**的阈值无关排序判别力。旧版“扩展窗口 F1 低于 always-positive（0.498 < 0.527）”的判断已随数据路径 bug 修复而**不再成立**。下一步仍缺：真正的 citywide 范围、观测事件降雨（当前合成常数导致 `PFI_h` 情景平坦）、FloodNet 留出验证。

---

## 6. 讨论 Discussion

相对 Svellingen et al. 2026，本工作的可对话差异是：

1. **开放标签**而非 PFIb；  
2. **空间块 CV 优先**（符合 GeoAI spatial CV 文献对泄漏的警告）；  
3. **尺度损失阶梯**建在开放热点上；  
4. **自适应**由 trained `PFI_h` 驱动；  
5. **语义澄清**：`PFI_h(c,r)` ≠ importance ≠ PFIb。

证据强度仅支撑“协议可跑通 + 尺度损失可见 + 单元数可降”，**不支撑**“全市可部署事件响应系统”。分类方面（2026-08-23 修订后）：小窗口（69.5% 正类，7 块）模型在 accuracy/F1 上**均超过**恒判正基线（0.808 > 0.687、0.864 > 0.813）；扩展窗口（`manhattan_expanded`，49.7% 正类，28 块）模型在 accuracy/F1 上**均超过**各自恒定多数类/always-positive 基线（0.824 > 0.503、0.832 > 0.663，折内均值）。留出阈值无关指标：小窗口 pooled ROC-AUC 0.741 / AP 0.803（随机基线 0.695），扩展窗口 pooled ROC-AUC 0.875 / AP 0.822（随机基线 0.497）——为**中等偏强**排序判别力，仍不升格为“强分类技能”，也不主张全市。311 报告偏差（arcgis_streetfloodtime 2010–2014 快照）、DEP 为模型导出（非观测）、潮汐岸线水文代理、合成降雨、平坦情景 PFI、小样本块不均（小窗口仅 7 块分 5 折），是主要科学风险。

独立 WebSearch（本轮）再次确认：Svellingen DOI 与 Jaccard≈0.14 / ~98% 效率叙述；spatial CV / GroupKFold 是 GeoAI 诚实评价的标准关切。ChatGPT 顾问若稍后回复，只合并**不冲突**建议；冲突时以 locked science 为准。

---

## 7. 结论 Conclusions

1. 开放标签 H3+ML + 空间块 CV 已产生两个试点（LM smoke `n=141`、扩展窗口 `n=956`）的可引用元数据，以及六张 SciencePlots 主图（工作流 F1、空间结果图 F2、源证据分解 F3、空间 CV F4、多分辨率空间 F5、分辨率效应 F6）。  
2. Jaccard 与自适应消融提供了与 PFIb 文献可**概念对话**、但不可**数值等同**的证据。  
3. `PFI_h(c,r)` 定义已绑定；情景响应与 I2 观测降雨为下一步（待补充）。  
4. **分类证据为“中等偏强判别力、仍不主张强分类技能/全市”**：小窗口 accuracy/F1（0.808/0.864）**超过**多数类（恒判正）平凡基线（0.687/0.813）；扩展窗口 accuracy/F1（0.824/0.832）**超过**恒定多数类（恒判负，0.503）与 always-positive F1（0.663），证据分 R²=0.346。留出阈值无关指标（pooled）：小窗口 ROC-AUC 0.741 / AP 0.803（随机基线 0.695），扩展窗口 ROC-AUC 0.875 / AP 0.822（随机基线 0.497）——均为**中等偏强**排序判别力，不升格为“强分类技能”，且非全市。旧版“扩展窗口 F1 低于 always-positive”的判断已随 2026-08-23 数据路径 bug 修复而废止。  
5. 可主张创新点见 `docs/paper/innovation_and_framework.md` 的 I1–I5；拒绝 PFIb 复现、Jaccard 0.14 等同、LM→citywide、雷达降雨、平坦情景判别、以及“分类有技能”的表述。

---

## 8. 局限 Limitations（务必留给审稿人/老师看）

| 局限 | 状态 |
|------|------|
| LM smoke n=141 ≠ citywide | 锁定 |
| 扩展窗口 `manhattan_expanded` n=956 ≠ citywide | 锁定（`outputs/expanded_primary_table.json`） |
| 类别失衡（修订后：小窗口 69.5% 正类 → 模型 accuracy/F1 均超恒判正基线；扩展窗口 49.7% 正类 → accuracy/F1 均超基线） | **锁定**（`outputs/classification_baselines.json` / `classification_baselines_expanded.json`，2026-08-23 修订 + 数据路径 bug 修复） |
| 合成 `event_raster`；I2 阻塞 | 锁定 |
| 情景 PFI_h 单元内极差=0 | 锁定（待补充修复） |
| FloodNet 默认关闭 | 锁定 |
| Oslo / fixture ≠ science | 锁定 |
| ROC-AUC / AP 留出判别指标 | **完成**（`models/*/spatial_cv_oof_predictions.csv`；小窗口 `outputs/smoke_discrimination.json`；扩展窗口 `outputs/expanded_primary_table.json`） |
| 工作流图 F1 schematic | **完成**（`docs/paper/figures/workflow_schematic.png`，SciencePlots + TNR） |
| 空间结果图 F2（观测/留出/PFI_h 三面板） | **完成**（`docs/paper/figures/spatial_maps.png`；仅视觉检视，非独立验证） |
| 源证据分解图 F3（DEP/311/HWM/composite 四面板） | **完成**（`docs/paper/figures/source_evidence_maps.png`；C3 源区分 provenance 的可视化证据，2026-08-23 新增） |
| 空间 CV 图 F4（Accuracy/F1 成对标记 + 三基线） | **完成**（`docs/paper/figures/spatial_cv_folds.png`；数据来自 `models/nyc_smoke/spatial_cv_folds.csv`） |
| 多分辨率空间图 F5（R10/R9/R8 开放标签分三面板） | **完成**（`docs/paper/figures/multi_resolution_spatial.png`；数据与 F6 同源，`nyc_h3_cells_r10_labels.parquet`） |
| 分辨率效应图 F6（分布小提琴 + Jaccard 矩阵） | **完成**（`docs/paper/figures/resolution_effects.png`；数值与 Jaccard 阶梯表一致） |
| 自适应消融补充图 S2（三柱单元数） | **完成**（`docs/paper/figures/supplementary/adaptive_ablation.png`；主文已表格化，图降级为补充） |
| ChatGPT web-search 顾问回复 | 已收到 R6–R10 活体评审（2026-08-17 人工粘贴），正在合并 |
| GitHub 远程仓库 | **已公开** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3（勿重复 `gh repo create`；勿 force-push） |

### 8.1 Paper vs report boundary (R6 audit)

| Belongs in **paper** (`manuscript.md`) | Belongs in **report** (this file) |
|----------------------------------------|-----------------------------------|
| Academic claims, methods narrative, live numbers with honest bounds | Local paths (`outputs/`, `models/nyc_smoke/`, configs) |
| Figure captions without repo-relative paths | Reproducibility commands, pytest gates, ChatGPT round process |
| Public GitHub URL + data availability | Cursor/ChatGPT collaboration logs, paste packages |
| 待补充 scientific gaps | 来龙去脉, download dates, machine-local session notes |

R6 applied: stripped advisor-chat URLs, nature-writing axes metadata, and `outputs/` / `models/nyc_smoke/` path literals from the manuscript body; retained those details here.

---

## 9. 产物路径清单

| Artifact | Path |
|----------|------|
| Report HTML | `docs/paper/report.html`, `report.html` |
| Report MD | `docs/paper/report.md` |
| Report PDF | `docs/paper/report.pdf` |
| Manuscript | `docs/paper/manuscript.md/.html/.pdf` |
| Figures | `docs/paper/figures/*.png` |
| Metadata | `models/nyc_smoke/run_metadata.json` |
| Classification baselines | `outputs/classification_baselines.json` / `.csv`（脚本 `scripts/compute_classification_baselines.py`） |
| Expanded-bbox primary table | `outputs/expanded_primary_table.json`（脚本 `scripts/run_expanded_study.py`） |
| Expanded-bbox baselines | `outputs/classification_baselines_expanded.json` / `.csv` |
| Expanded-bbox models/folds | `models/nyc_expanded/`（`run_metadata.json`, `spatial_cv_folds.csv`） |
| Literature conclusions | `artifacts/literature_architecture_conclusions.md` |
| ChatGPT brief | `artifacts/chatgpt_literature_brief.md` |
| Collaboration | `artifacts/chatgpt_collaboration_report.md` |
| Acceptance | `artifacts/acceptance_report_*.md` |

---

*生成说明：数值均从上述 CSV/JSON 抄录或脚本聚合；若与磁盘文件冲突，以磁盘 live 文件为准。*
