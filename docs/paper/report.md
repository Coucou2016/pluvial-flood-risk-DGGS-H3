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
| Open labels（开放标签） | DEP 雨洪多边形、311 积水点、USGS Ida HWM 等公开图层；**不是**保险公司 PFIb |
| PFIb（building-level Pluvial Flood Index） | 7Analytics / Svellingen 等所用建筑级雨洪指数（保险损害驱动）；本项目**不使用** |
| PFI_h(c,r) | 模型在降雨条件 \(r\) 下对六边形单元 \(c\) 的洪水概率/指数预测；**不是**特征重要性，也**不是** PFIb（注意：Svellingen 等也用 `PFI_h` 表示其 H3 聚合后的 PFIb；本项目的 `PFI_h(c,r)` 是独立定义，二者符号同名但语义不同） |
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

在 H3 分辨率 R9 上组装 **n_cells = 141** 个六边形单元，`assembly_mode=opendata`。主（**分块评价**）指标为 **spatial H3-block CV（空间 H3 块交叉验证）**：准确率均值 **0.783756 ± 0.069280**，F1 均值 **0.865748**（来源：`models/nyc_smoke/run_metadata.json`，`created_utc=2026-08-16T06:36:48Z`）。**关键诚实修正（2026-08-17）：** 留出样本正类占比 **80.1%**，恒判正的多数类平凡基线在同样折上可达 accuracy **0.808**、F1 **0.893**，**高于**模型的 0.784 / 0.866——故这两个数**不得**被称为“分类技能”（来源：`outputs/classification_baselines.json`）。尺度损失用开放标签 **Jaccard ladder** 诊断：细 R10→粗 R8 的 **mean** 聚合 Jaccard = **0.1667**（不得写成“复现了 Svellingen 的 0.14”）。自适应相对均匀细网格（R11）单元数比 **adaptive_cell_count_ratio ≈ 0.569**。

**诚实缺口（待补充）：** (1) I2 观测事件降雨仍阻塞，`rainfall_source=event_raster` 为合成常数钩子；(2) `outputs/pfi_h_scenarios.csv` 四情景（25/40/75/100 mm/h）下，**单元内 PFI_h 极差 = 0**，情景均值同为 ≈0.802888，故**不宣称**已观察到降雨条件判别力；(3) LM ≠ citywide；(4) ChatGPT 浏览器 MCP 本会话不可用，顾问 web-search 回复待人工粘贴 brief。

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
| DEP stormwater flood polygons | 开放雨洪标签之一 |
| Building footprints | 建筑密度等 |
| USGS Ida high-water marks | 点状开放标签 |
| 311 flooding points | 点状开放标签（报告偏差风险） |
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

- **主学习器：** 梯度提升分类器 + 连续风险回归器。  
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
**如何读：** 从左到右四列——(1) 开放多源输入（开放标签 + 静态特征 + 降雨条件 r）；(2) H3 组装（R9，带 provenance 标签）；(3) 学习与分块评价（梯度提升 + H3 块 GroupKFold 空间 CV + 常量类基线（恒判正/恒判负）+ 逻辑/积水规则基线）；(4) 诊断与输出（`PFI_h(c,r)`、Jaccard 尺度损失阶梯、自适应加密、Sandy 负对照检查）。FEMA Sandy 是一条**虚线旁路**，绕过学习框、只进入负对照诊断，绝非训练标签。  
**意义：** 一张图讲清整条协议与「证据—边界」纪律，帮助审稿人快速定位每一步对应的结果小节。  
**结论：** `PFI_h(c,r)` 是模型输出，不是特征重要性，也不是 PFIb；当前情景响应平坦（定义/接口已绑定，响应待观测降雨）；证据仅限两个 Manhattan 开放数据试点，非全市。

---

## 4. 过程 Process（怎么跑到这些图）

1. 下载/校验 `data/raw/nyc/`，写入 `DOWNLOAD_MANIFEST.json` / `DATA_SOURCES.md`。  
2. `build_nyc_h3.py --no-fixtures` → `data/processed/nyc_h3_cells.parquet`（opendata）。  
3. `pluvial-nyc-smoke` → `models/nyc_smoke/*`、`outputs/*`（空间 CV、Jaccard、自适应、情景、负对照）。  
4. SciencePlots + TNR 重绘四图到 `docs/paper/figures/`（并同步 `artifacts/figures/`）。  
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
| accuracy mean ± std | 0.783756 ± 0.069280 |
| F1 mean | 0.865748 |
| R² mean ± std | 0.030333 ± 0.342841 |
| MAE mean | 0.332182 |
| random_split_val_accuracy（诊断） | 0.689655 |
| 留出正类占比（prevalence） | 0.8014 |
| 多数类（恒判正）基线 accuracy | **0.808** |
| 多数类（恒判正）基线 F1 | **0.893** |
| 模型是否超过多数类基线 acc / f1 | **否 / 否** |
| 留出 ROC-AUC（pooled） | **0.683** |
| 留出 AP（pooled） | **0.861**（随机基线 = 正类占比 0.801） |

**来龙去脉：** smoke 跑完后，训练脚本把 GroupKFold 各折平均写入 metadata；随后 `scripts/compute_classification_baselines.py` 读取 `spatial_cv_folds.csv`，对每折计算“全部判正”“全部判负”两种平凡基线并写入 `outputs/`。这是论文/报告里**唯一优先引用的评价汇总**，且**必须**连同类别占比与多数类基线一起引用。  
**如何读：** 先看正类占比（0.8014，即 80% 留出单元为正），再看多数类基线（恒判正 acc 0.808 / F1 0.893），最后才看模型分数（0.784 / 0.866）。模型分数**低于**多数类基线，说明阈值化的 accuracy/F1 未超过“闭眼判洪”；但留出 ROC-AUC 0.683 > 0.5、AP 0.861 仅略高于 0.801 随机基线，提示存在**中等且有限**的排序判别力，不能据此主张“分类技能”。R² 接近 0 也说明连续风险回归几乎无解释力。随机划分准确率略低/不同，仅提示“换协议分数会变”，不能当主结果。  
**意义：** 空间块留出让评价设计更诚实，但它本身不产生技能证据；在类别严重失衡时，accuracy/F1 必须与平凡基线对照，否则会被虚高。  
**结论（允许）：** LM smoke 上协议可跑通（能训练、能分块评价、能出表）。  
**结论（禁止）：** 全市技能；“强分类判别力”（阈值化 accuracy/F1 **未超过**多数类基线，ROC-AUC/AP 仅为中等）；用随机划分替换空间 CV；“已解决事件响应预报”。

### 表 2 · 逐折明细

**来源：** `models/nyc_smoke/spatial_cv_folds.csv`

| fold | n_train | n_test | accuracy | f1 | r2 | mae |
|------|---------|--------|----------|-----|-----|-----|
| 0 | 92 | 49 | 0.755 | 0.850 | −0.440 | 0.409 |
| 1 | 116 | 25 | 0.760 | 0.850 | −0.089 | 0.369 |
| 2 | 119 | 22 | 0.773 | 0.872 | −0.021 | 0.376 |
| 3 | 120 | 21 | 0.714 | 0.813 | 0.082 | 0.307 |
| 4 | 117 | 24 | 0.917 | 0.944 | 0.620 | 0.199 |

**来龙去脉：** 每个 fold 留出 1–2 个粗 H3 父块；测试块 ID 列在 CSV 的 `test_block_ids`。  
**如何读：** Fold4 准确率 0.917 明显高于其他折——这正是必须同时报告 **std** 的原因：块大小与正负类比例不均时，单折会跳动。  
**意义：** 展示评价协议的折间不稳定性，而不是“挑最好一折”。  
**结论：** 均值有效，但外部效度仍受小样本与块不均限制。

#### 图 2 · `docs/paper/figures/spatial_cv_folds.png`

**来龙去脉：** 由 `spatial_cv_folds.csv` 经 `src/pluvial_flood_risk/figures.py`（SciencePlots + TNR）绘制 Accuracy/F1 成对柱。  
**如何读：** 横轴 fold_id；纵轴 0–1；每折两柱。  
**意义：** 把表 2 变成可一眼比较的稳定性图。  
**结论：** 多数折 Accuracy≈0.71–0.77，Fold4 抬高均值；与表 1 一致。仍是 LM smoke。

---

### 表 3 · Jaccard 尺度损失阶梯

**来源：** `outputs/jaccard_by_resolution.csv`（fine_res=10，hotspot_quantile=0.9）

| coarse | agg | jaccard | f1 |
|--------|-----|---------|-----|
| 8 | mean | 0.1667 | 0.2857 |
| 8 | max | 1.0000 | 1.0000 |
| 8 | p90 | 1.0000 | 1.0000 |
| 9 | mean | 0.9767 | 0.9882 |
| 9 | max | 1.0000 | 1.0000 |
| 9 | p90 | 0.9767 | 0.9882 |

附：细网格 n_fine=991，热点 n_hotspot_fine=571（阈值）。

**来龙去脉：** 在细 R10 上取高风险热点集合，再按父单元用 mean/max/p90 聚合后与粗网格热点比 Jaccard/F1。目的是诊断 **MAUP / scale-loss**，不是复现 PFIb 文献数字。  
**如何读：** 关注 **mean@R8=0.1667**：粗尺度平均抹平了细热点；max/p90 接近 1 是因为极值保留机制，**不是**“粗网格完美”。  
**意义：** 说明“沟通用粗网格”与“安全关键细热点”不可混为一谈——这与 Svellingen 的尺度权衡叙事**概念对话**，但标签栈不同。  
**结论（允许）：** 开放标签下，mean 上卷到 R8 会严重改变热点集合。  
**结论（禁止）：** “我们得到了与 Svellingen 相同的 Jaccard 0.14”；把 max/p90=1 写成模型完美。

#### 图 3 · `docs/paper/figures/jaccard_by_resolution.png`

**来龙去脉：** 同 CSV 的 SciencePlots 折线（左 Jaccard、右 F1；线型区分 agg）。  
**如何读：** 随 coarse_res 变粗，看 mean 线是否下降。  
**意义：** 可视化尺度损失。  
**结论：** mean 在 R8 损失最大；禁止与 PFIb 的 0.14 数值等同。

---

### 表 4 · 自适应 vs 固定 / 均匀细网格

**来源：** `outputs/adaptive_vs_fixed_ablation.csv`

| Field | Value |
|-------|-------|
| score_col | PFI_h |
| n_fixed_coarse (R9) | 141 |
| n_adaptive_mixed | 3933 |
| n_uniform_fine (R11) | 6909 |
| adaptive_cell_count_ratio (adaptive/uniform) | 0.569257 |
| parents_refined | 79 |
| score_quantile | 0.8 |
| coarse→fine | 9→11 |

**来龙去脉：** 训练后用 `PFI_h` 筛高分父单元，再加密到 R11，形成混合分辨率网格；与“全部留在 R9”和“全部升到 R11”对比单元数。  
**如何读：** 141 → 3933 → 6909；比率 0.569 表示自适应约为均匀细网格 **57%** 的单元数。  
**意义：** 在计算预算与局部细化之间的工程折中；分数来源写明为 trained PFI_h。  
**结论（允许）：** 本 smoke 设定下自适应降低均匀细网格单元数约四成多。  
**结论（禁止）：** 全市算力节省；自适应已提高泛化技能（本表是**单元数**消融，不是技能提升表）。

#### 图 4 · `docs/paper/figures/adaptive_ablation.png`

**来龙去脉：** 三柱条形图对应表 4 三个单元数。  
**如何读：** 中间柱应介于左右之间。  
**意义：** 一眼看到成本折中。  
**结论：** 与表 4 一致；非全市声明。

---

### 表 5 · Sandy 负对照

**来源：** `outputs/negative_control.json`

| Field | Value |
|-------|-------|
| n_cells | 141 |
| n_coastal / n_pluvial / n_both | 31 / 71 / 23 |
| n_coastal_only / n_pluvial_only | 8 / 48 |
| n_neither | 62 |
| frac_coastal_only | 0.0567 |
| pluvial_minus_coastal_mean_score | 0.1198 |
| score_col | flood_risk |
| assembly_mode | opendata |

**来龙去脉：** 把 FEMA Sandy 沿海淹没与开放 pluvial 标签叠在同一批 H3 单元上，检查空间是否完全重合。  
**如何读：** `n_both=23` 说明有重叠；`n_coastal_only=8` 说明存在“只沿海、不落进 pluvial 标签”的单元；均值分差 ≈0.12。  
**意义：** 负对照提醒模型不要把 coastal 过程误当成 pluvial 训练信号。  
**结论（允许）：** 标签空间不完全重合；差分提示分离检查有信号。  
**结论（禁止）：** 已验证因果分离；可用 Sandy 当训练标签。

---

### 5.6 PFI_h 降雨情景（诚实缺口 · 待补充）

**来源：** `outputs/pfi_h_scenarios.csv`（564 行 = 141 单元 × 4 情景）

| scenario | rainfall_mm_h | mean PFI_h |
|----------|---------------|------------|
| moderate | 25 | 0.802888 |
| heavy | 40 | 0.802888 |
| Ida-like | 75 | 0.802888 |
| extreme | 100 | 0.802888 |

**核验：** 按 `h3_index` 分组，`max(PFI_h)-min(PFI_h)` 的全局最大值为 **0.0**。  
**来龙去脉（根因已确诊，2026-08-17）：** 情景循环本身正确——只改 `rainfall_mm_h` 再预测，产物里 4 个情景的 `rainfall_mm_h` 也确实分别是 25/40/75/100。平坦的真正原因是**训练阶段降雨是常数**：训练表 `data/processed/nyc_h3_cells.parquet` 的 141 个单元 `rainfall_mm_h` 全部为 **75.0**（`rainfall_source=event_raster` 的合成常数钩子），因此 `rainfall_mm_h` 在训练特征矩阵中方差为 0；`GradientBoostingClassifier` 对该列的特征重要性为 **0.0**（`models/nyc_smoke/classifier.joblib`）。模型从未见过降雨变化，自然无法对情景做出响应。  
**结论：** **定义保留**；**经验判别力本轮不成立**，且成因不是 bug 而是“训练降雨恒为常数”。要得到非零响应，必须先引入 I2 观测事件降雨（多强度、非合成 provenance），再重训；在此之前禁止在摘要写“情景响应已验证”。

### 5.7 扩展 bbox 主表（`manhattan_expanded`，`n=956`）

**来源：** `outputs/expanded_primary_table.json`、`models/nyc_expanded/spatial_cv_folds.csv`、`outputs/classification_baselines_expanded.{json,csv}`；原始数据在 `data/raw/nyc_expanded/`（`DOWNLOAD_MANIFEST.json` 可溯源）。

**来龙去脉：** §5.1 的 `n=141` 表只覆盖 Lower Manhattan 极小窗口，正类占比高达 80.1%，被 ChatGPT R8 评审判为“material issue”——因为 80% 的正类意味着“永远说会淹”的平凡基线就能拿到 0.808 accuracy / 0.893 F1，模型反而打不过它。为检验这是否只是“极小 bbox 落在 DEP 洪泛多边形内”造成的**范围敏感现象（extent-sensitivity 假设）**，本小节把同样的开放数据协议跑在更大的 `manhattan_expanded` 范围（`[-74.03, 40.68, -73.94, 40.80]`，约 0.09° × 0.12°，从曼哈顿下城向上城/中城南扩展），得到 `n=956` 个 R9 单元、28 个空间块。注意：这一步只“扩大范围再跑一次”，**不构成**对“小窗口 80% 正类是伪象”的证明——除非后续量化两个范围下各标签分量（DEP/311/Ida）的覆盖差异。

**如何读：** 下表与 §5.1 表 1 同构，便于直接对照“小窗口 vs 扩展窗口”。

| Metric | 扩展窗口 (`manhattan_expanded`) | 小窗口 (LM smoke) |
|--------|-------------------------------|-------------------|
| n_cells | **956** | 141 |
| spatial_cv_n_blocks | **28** | 7 |
| spatial_cv_n_folds | 5 | 5 |
| 正类占比（held-out） | **0.479** | 0.801 |
| spatial_cv_accuracy_mean ± std | **0.642 ± 0.148** | 0.784 ± 0.069 |
| spatial_cv_f1_mean | **0.608** | 0.866 |
| spatial_cv_r2_mean ± std | **0.525 ± 0.112** | 0.030 ± 0.343 |
| spatial_cv_mae_mean | **0.112** | 0.332 |
| random_split_val_accuracy（仅诊断） | 0.667 | 0.690 |
| always-positive accuracy | **0.479** | 0.808 |
| always-positive F1（折内均值） | **0.641** | 0.893 |
| always-negative accuracy | **0.521** | 0.192 |
| always-negative F1（正类） | 0.000 | 0.000 |
| 恒定多数类（真多数类） | 恒判负，acc 0.521 | 恒判正，acc 0.808 |
| 模型是否超过恒定多数类 accuracy | **是（0.642 > 0.521）** | 否（0.784 < 0.808） |
| 模型是否超过 always-positive F1 | 否（0.608 < 0.641） | 否（0.866 < 0.893） |
| ROC-AUC（pooled，留出） | **0.703** | 0.683 |
| AP / average precision（pooled，留出） | **0.723** | 0.861 |
| 随机 AP 基线（=正类占比） | 0.479 | 0.801 |

**逐折明细（`models/nyc_expanded/spatial_cv_folds.csv`）：**

| fold | n_test | 正/负 | accuracy | f1 | r2 |
|------|--------|-------|----------|----|----|
| 0 | 191 | 119 / 72 | 0.801 | 0.832 | 0.486 |
| 1 | 191 | 66 / 125 | 0.419 | 0.442 | 0.713 |
| 2 | 191 | 97 / 94 | 0.759 | 0.736 | 0.533 |
| 3 | 190 | 73 / 117 | 0.516 | 0.343 | 0.525 |
| 4 | 193 | 103 / 90 | 0.715 | 0.689 | 0.366 |

**意义（为什么这个表重要）：**

1. **类别失衡随空间范围变化。** 扩展窗口正类占比 47.9%，接近均衡；这提示小窗口的 80.1% 正类很可能是“极小 bbox 落在 DEP 洪泛多边形内”造成的范围敏感现象（extent-sensitivity 假设），但本报告**尚未量化**两个范围下各标签分量（DEP/311/Ida）的覆盖差异，因此不宣称“已证明”小窗口占比是伪象。
2. **accuracy 超过恒定多数类基线。** 扩展窗口模型 0.642 的 accuracy 高于恒定多数类（恒判负）0.521，也高于 always-positive 0.479。这是阈值化 accuracy 层面的证据，但**不等同于**阈值无关的判别力证明；它与小窗口“打不过平凡基线”形成对比，但“可迁移判别信息”仍需真正的空间/外部迁移证据才能主张。
3. **连续风险 R² 从近零变为 0.525。** 小窗口 R²≈0.030，扩展窗口 R²≈0.525，说明在更大、更均衡的样本上连续回归出现正信号。但单个扩展试点**不能**归因于“样本规模或空间覆盖不足是小窗口 R² 近零的原因”——该差异只表明范围敏感，未识别其具体成因。
4. **F1 仍低于 always-positive 比较器（0.608 < 0.641，折内均值）。** F1 是对正类的调和平均；在近均衡设定下，“永远说会淹”仍有 recall=1、precision≈0.479，折内 F1≈0.641。模型为了提升精度牺牲了部分 recall，导致 F1 略低于该比较器。因此单看 F1，**不能主张“分类技能”**。
5. **阈值无关判别指标为中等。** 留出 pooled ROC-AUC=0.703（>0.5）、AP=0.723，后者明显高于其随机基线 0.479。这提示存在**中等程度**的留出排序判别力，且相对于随机基线，扩展窗口（更均衡）比小窗口（AP 0.861 仅略高于随机基线 0.801）更有说服力。但 ROC-AUC/AP 只回答“排序是否优于随机”，不回答“正类 F1 是否优于 always-positive”，故总体结论仍为**判别力中等、而非强**。

**结论（honest）：** 扩展窗口主表**不是全市结果**（仍是曼哈顿中城南+下城北的试点），但它把“小窗口因类别失衡而打不过平凡基线”这一最严重短板缓解了：模型在 accuracy 上超过恒定多数类基线（0.642 > 0.521），连续 R² 变为正信号（0.525），且留出 ROC-AUC 0.703 / AP 0.723 给出**中等**阈值无关排序判别力（相对随机基线 0.479 更有意义）。但正类 F1 仍低于 always-positive 比较器（0.608 < 0.641），故**分类证据混合、判别力中等而非强、仍不主张全市“分类技能”**。下一步仍缺：真正的 citywide 范围、观测事件降雨（当前合成常数导致 `PFI_h` 情景平坦）、FloodNet 留出验证。

---

## 6. 讨论 Discussion

相对 Svellingen et al. 2026，本工作的可对话差异是：

1. **开放标签**而非 PFIb；  
2. **空间块 CV 优先**（符合 GeoAI spatial CV 文献对泄漏的警告）；  
3. **尺度损失阶梯**建在开放热点上；  
4. **自适应**由 trained `PFI_h` 驱动；  
5. **语义澄清**：`PFI_h(c,r)` ≠ importance ≠ PFIb。

证据强度仅支撑“协议可跑通 + 尺度损失可见 + 单元数可降”，**不支撑**“全市可部署事件响应系统”。分类方面：小窗口（80% 正类）模型打不过平凡基线（accuracy/F1 均低于恒判正基线）；扩展窗口（`manhattan_expanded`，47.9% 正类，28 块）模型在 accuracy 上**超过**恒定多数类（恒判负）基线（0.642 > 0.521），但正类 F1 仍低于 always-positive 比较器（0.608 < 0.641，折内均值）。留出阈值无关指标为**中等**：小窗口 pooled ROC-AUC 0.683 / AP 0.861（随机基线 0.801），扩展窗口 pooled ROC-AUC 0.703 / AP 0.723（随机基线 0.479）。故**分类证据混合、判别力中等而非强、仍不主张全市“分类技能”**。311 报告偏差、潮汐岸线水文代理、合成降雨、平坦情景 PFI、小样本块不均（小窗口仅 7 块分 5 折），是主要科学风险。

独立 WebSearch（本轮）再次确认：Svellingen DOI 与 Jaccard≈0.14 / ~98% 效率叙述；spatial CV / GroupKFold 是 GeoAI 诚实评价的标准关切。ChatGPT 顾问若稍后回复，只合并**不冲突**建议；冲突时以 locked science 为准。

---

## 7. 结论 Conclusions

1. 开放标签 H3+ML + 空间块 CV 已产生两个试点（LM smoke `n=141`、扩展窗口 `n=956`）的可引用元数据，以及四张 SciencePlots 主图（工作流 F1、空间 CV F2、Jaccard F3、自适应 F4）。  
2. Jaccard 与自适应消融提供了与 PFIb 文献可**概念对话**、但不可**数值等同**的证据。  
3. `PFI_h(c,r)` 定义已绑定；情景响应与 I2 观测降雨为下一步（待补充）。  
4. **分类证据混合、判别力中等而非强、仍不主张“分类技能”**：小窗口 accuracy/F1（0.784/0.866）低于多数类平凡基线（0.808/0.893）；扩展窗口 accuracy 超过恒定多数类（恒判负）基线（0.642 > 0.521）且连续 R²=0.525，但正类 F1（0.608）仍低于 always-positive 比较器（0.641，折内均值）。留出阈值无关指标（pooled）：小窗口 ROC-AUC 0.683 / AP 0.861（随机基线 0.801），扩展窗口 ROC-AUC 0.703 / AP 0.723（随机基线 0.479）——均为**中等**排序判别力，不升格为“强分类技能”。  
5. 可主张创新点见 `docs/paper/innovation_and_framework.md` 的 I1–I5；拒绝 PFIb 复现、Jaccard 0.14 等同、LM→citywide、雷达降雨、平坦情景判别、以及“分类有技能”的表述。

---

## 8. 局限 Limitations（务必留给审稿人/老师看）

| 局限 | 状态 |
|------|------|
| LM smoke n=141 ≠ citywide | 锁定 |
| 扩展窗口 `manhattan_expanded` n=956 ≠ citywide | 锁定（`outputs/expanded_primary_table.json`） |
| 类别失衡（小窗口 80% 正类 → 模型未超多数类基线；扩展窗口 47.9% → accuracy 超基线、F1 未超） | **锁定**（`outputs/classification_baselines.json` / `classification_baselines_expanded.json`） |
| 合成 `event_raster`；I2 阻塞 | 锁定 |
| 情景 PFI_h 单元内极差=0 | 锁定（待补充修复） |
| FloodNet 默认关闭 | 锁定 |
| Oslo / fixture ≠ science | 锁定 |
| ROC-AUC / AP 留出判别指标 | **完成**（`models/*/spatial_cv_oof_predictions.csv`；小窗口 `outputs/smoke_discrimination.json`；扩展窗口 `outputs/expanded_primary_table.json`） |
| 工作流图 F1 schematic | **完成**（`docs/paper/figures/workflow_schematic.png`，SciencePlots + TNR） |
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
