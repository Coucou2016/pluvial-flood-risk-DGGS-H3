# 审查文档（Audit）：数据真实性、准确性与完整性证据

**用途：** 本文档用于证明手稿 `manuscript.md` 与研究报告 `report.md` 中的所有数字，均为**本仓库自身代码在本机数据上运行所得**，而非从参考文献（尤其 Svellingen et al. 2026 IJDRR 及其 PFIb / Jaccard 0.14 数字）或任何第三方论文中抄录；并证明结果**可逐条复算、可对账、无“做一半臆断一半”**。

**审查对象：** `docs/paper/manuscript.md`、`docs/paper/report.md`、`README.md` 中的全部量化结论。

> **版本说明（2026-08-19 W1/W2 写作重写）：** 手稿 `manuscript.md` 在 2026-08-19 进行了**仅写作/逻辑/投稿体例**的重写（编号引用、单主线叙事、创新点重组为 "H3-native 学习-评估架构"），**所有数字、结果与核心结论未做任何改动**。因此本文档 §2 的逐条对账（按数值与产物字段，而非章节号）依然有效；本重写仅使手稿章节号从旧 8 章结构变为新 6 章结构（旧 §6 Results → 新 §4 Results；旧 §7 Discussion → 新 §5 Discussion）。下文引用的产物字段路径均未变。

**口径约定（贯穿全文）：**

- **本方法自己算出的数字**：全部来自 `src/pluvial_flood_risk/` 与 `scripts/` 在本机 `data/raw/` 上的运行产物（`outputs/*.json/csv`、`models/*/*.csv/joblib`、`data/processed/*.parquet`）。
- **明确的“待补充 / synthetic”项**：观测事件降雨（当前为合成常数）、FloodNet 留出传感器、citywide 范围。这些在文中以“尚未建立 / 未主张 / 待补充”显式标注，**不做臆断性数值填充**。
- **绝不使用他人数字**：本工作**不复现 PFIb**、**不引用 Svellingen 的 Jaccard 0.14 或 ~98% 效率作为自己的结果**。文中仅把 0.14 作为“不同标签/分辨率/热点定义”的概念对照，并明确禁止数值等同。

---

## 1. 真实性（Authenticity）：数字来自自己的数据与代码

### 1.1 数据获取链（可溯源）

| 层 | 文件/来源 | 状态 | 说明 |
|----|-----------|------|------|
| 配置 | `configs/nyc.yaml` | 本仓库 | 定义 bbox（`lower_manhattan` / `manhattan_expanded`）、`resolution: 9`、`random_seed: 42`、5 折空间 CV、标签/降雨场景 |
| 下载 | `scripts/download_nyc_data.py` | 本仓库 | 下载 USGS 3DEP DEM、DEP 洪泛多边形、建筑、311、Ida HWM、Sandy、NLCD、NHD 等开放图层 |
| 下载清单 | `data/raw/nyc/DOWNLOAD_MANIFEST.json`、`data/raw/nyc_expanded/DOWNLOAD_MANIFEST.json` | 本机生成 | 逐层记录状态/来源/日期，是“这些文件确实存在且为本机下载”的凭证 |
| 数据说明 | `data/raw/DATA_SOURCES.md` | 本仓库 | 逐层来源 + observed / synthetic / fixture 三态约定 |

**关键来源（非 PFIb、非保险索赔）：**

- 高程：USGS 3DEP（`dem.tif`）；不透水：Esri NLCD 分数不透水（`impervious.tif`）；水系：NHDPlus HR（`hydro_streams.geojson`，`dist_stream_m` 为岸线/水域距离代理）。
- 标签：NYC DEP 雨水洪泛多边形（`dep_stormwater_flood.geojson`，ArcGIS Hub）、NYC 311 街道积水点（`flooding_311.geojson`，ArcGIS/CDN 镜像）、USGS 飓风 Ida 高水位点（`usgs_ida_hwm.geojson`，ScienceBase DOI `10.5066/P9OMBJPQ`）。
- 负对照：FEMA Sandy 风暴潮淹没区（`fema_sandy.geojson`）——**仅负对照，绝不作为训练标签**。
- 降雨：`event_rainfall.tif` 为**合成常数 75 mm/h 输入**，非雷达/雨量计——已在文末与图中显式声明。

### 1.2 计算链（谁产生了这些数字）

```
configs/nyc.yaml
   └─ scripts/run_expanded_study.py  (bbox=manhattan_expanded, R9)
        ├─ assemble_h3_table()   → data/processed/nyc_h3_cells_expanded.parquet
        ├─ run_training()        → models/nyc_expanded/{classifier,regressor}.joblib
        │                          models/nyc_expanded/spatial_cv_folds.csv
        │                          models/nyc_expanded/spatial_cv_oof_predictions.csv
        │                          models/nyc_expanded/run_metadata.json
        └─ _constant_baselines() → outputs/classification_baselines_expanded.{json,csv}
                                   outputs/expanded_primary_table.json
```

每一个手稿数字都能定位到上述产物中的**某个具体字段**（见 §2 对账表）。

### 1.3 “不是别人论文里的数字”的证据

| 证据 | 内容 |
|------|------|
| 标签来源 | `expanded_primary_table.json → data_provenance = "observed"`，`assembly_mode = "opendata"`（非 PFIb/保险） |
| 明确排除 | `data/raw/DATA_SOURCES.md`：“This repository does not reproduce 7Analytics PFIb and does not ship insurance claims.” |
| Jaccard 说明 | 手稿 Results §4.2 / Discussion §5.2 与图注明确：0.167 是本仓库开放标签在 R10→R8 mean 聚合下的结果，**不得**等同 Svellingen 0.14 |
| 合成项显式标注 | 降雨为合成常数、情景 `PFI_h` 平坦（within-cell range = 0）——文中作为“未演示降雨条件判别”如实报告，而非编造响应 |

---

## 2. 准确性（Accuracy）：逐条对账

### 2.1 扩展窗口（`manhattan_expanded`，n=956）主表对账

来源：`outputs/expanded_primary_table.json`（`spatial_cv` 与 `constant_baselines` 两个字段块）。

| 手稿数字 | 产物字段 | 产物原始值 | 对账 |
|----------|----------|-----------|------|
| n=956 | `n_cells` | 956 | ✓ |
| 正类占比 0.479 | `constant_baselines.positive_prevalence` | 0.4790794979079498 = 458/956 | ✓ |
| accuracy 0.642 ± 0.148 | `spatial_cv_accuracy_mean/std` | 0.6419745944 / 0.1483789803 | ✓ |
| F1 0.608 | `spatial_cv_f1_mean` | 0.6083648652 | ✓ |
| R² 0.525 ± 0.112 | `spatial_cv_r2_mean/std` | 0.5246602554 / 0.1115798249 | ✓ |
| MAE 0.112 | `spatial_cv_mae_mean` | 0.1122533611 | ✓ |
| always-positive acc 0.479 | `always_positive_acc_mean` | 0.4788658147（折内均值） | ✓ |
| always-positive F1 0.641 | `always_positive_f1_mean` | 0.6412101499（折内均值） | ✓ |
| 恒定多数类（恒判负）acc 0.521 | `always_negative_acc_mean` = `majority_acc_mean` | 0.5211341853 | ✓ |
| 多数类 = 负类 | `majority_class` | `"negative"`（458 正 / 498 负） | ✓ |
| 模型超多数类 accuracy | `model_beats_majority_acc` | true（0.642 > 0.521） | ✓ |
| 模型未超 always-positive F1 | `model_beats_always_positive_f1` | false（0.608 < 0.641） | ✓ |

**R11 修正说明：** 早期脚本把“always-positive（恒判正）”误标为“majority（多数类）”。当正类占比 47.9%（<50%）时，真正多数类是**负类**。本轮已改为**同时显式报告 always-positive 与 always-negative 两个常量分类器**，并据 pooled 类别数推导真多数类，且基线全部改为**折内均值**（与模型 F1 的聚合口径一致）。修正后结论不变且更准确：模型 accuracy 超过真多数类（0.642 > 0.521），但正类 F1 仍低于 always-positive 比较器（0.608 < 0.641）。

### 2.2 逐折明细对账

来源：`models/nyc_expanded/spatial_cv_folds.csv`（与 `expanded_primary_table.json` 内嵌一致）。

| fold | n_test | 正/负 | accuracy | f1 | r2 |
|------|--------|-------|----------|----|----|
| 0 | 191 | 119/72 | 0.801 | 0.832 | 0.486 |
| 1 | 191 | 66/125 | 0.419 | 0.442 | 0.713 |
| 2 | 191 | 97/94 | 0.759 | 0.736 | 0.533 |
| 3 | 190 | 73/117 | 0.516 | 0.343 | 0.525 |
| 4 | 193 | 103/90 | 0.715 | 0.689 | 0.366 |

（正/负合计 458/498，与 §2.1 完全一致；5 折 test 合计 956。）

### 2.3 小窗口（Lower Manhattan，n=141）对账

来源：`models/nyc_smoke/spatial_cv_folds.csv` + `outputs/classification_baselines.json`。

| 手稿数字 | 产物字段 | 原始值 | 对账 |
|----------|----------|--------|------|
| 正类占比 0.801 | `overall_positive_prevalence` | 0.8014184397 | ✓ |
| accuracy 0.784 ± 0.069 | `spatial_cv_accuracy_mean/std` | 0.783756 / 0.069 | ✓ |
| F1 0.866 | `spatial_cv_f1_mean` | 0.8657478632 | ✓ |
| always-positive（多数类）acc 0.808 | `always_positive_mean_acc` | 0.8081669759 | ✓ |
| always-positive F1 0.893 | `always_positive_mean_f1` | 0.8933652954 | ✓ |
| always-negative acc 0.192 | `always_negative_mean_acc` | 0.1918330241 | ✓ |

（小窗口正类 80.1% 占多数，故 always-positive 即真多数类，与小窗口“打不过平凡基线”的结论一致。）

### 2.4 阈值无关判别指标（ROC-AUC / AP）

由 `spatial_block_cv_metrics`（`src/pluvial_flood_risk/spatial_cv.py`）在**留出折**上逐 cell 收集 `y_true` 与 `predict_proba`，写出 `models/<name>/spatial_cv_oof_predictions.csv`，并报 pooled 与折内均值的 ROC-AUC 与 average precision（AP）。小窗口由 `scripts/compute_oof_discrimination.py` 复算归档，扩展窗口由 `scripts/run_expanded_study.py` 直接产出。

| 试点 | ROC-AUC pooled | ROC-AUC 折内均值 ± std | AP pooled | AP 折内均值 ± std | 随机 AP 基线（=正类占比） |
|------|----------------|------------------------|---------------|------------------------|-------------------------------|
| LM smoke（n=141） | **0.683** | 0.722 ± 0.143 | **0.861** | 0.903 ± 0.065 | 0.801 |
| expanded（n=956） | **0.703** | 0.672 ± 0.170 | **0.723** | 0.661 ± 0.223 | 0.479 |

**解读（honest）：** 两个试点均存在**中等程度**的留出阈值无关排序判别力（ROC-AUC 均 > 0.5）；在更均衡的扩展窗口，AP 0.723 明显高于其随机基线 0.479，而小窗口 AP 0.861 仅略高于其随机基线 0.801。因此结论表述为“**判别力中等、而非强；仍不主张全市分类技能**”，且正类 F1 在两个试点都低于 always-positive 比较器。该指标用于如实回答“判别力是否建立”，不替代 accuracy/F1，也不用于夸大。

---

## 3. 完整性（Completeness）：代码完整、无臆断

### 3.1 代码覆盖

| 环节 | 代码 | 测试 |
|------|------|------|
| 空间块 CV | `spatial_cv.py`（GroupKFold over H3 parent） | `tests/test_spatial_cv.py` |
| 度量（含 ROC-AUC / AP） | `metrics.py`、`spatial_cv.py` | `tests/test_ablation_and_cv_folds.py` |
| 基线（常量/逻辑/ponding） | `baselines.py`、`scripts/run_expanded_study.py` | `tests/test_baselines.py` |
| 可复现性（固定 seed） | `model.py`（RANDOM_SEED=42） | `tests/test_reproducibility.py` |
| 端到端 | `pipeline.py` | `tests/test_pipeline_smoke.py`、`tests/test_model_artifacts.py` |
| 图 | `figures.py`（`plot_workflow_schematic` 等） | `tests/test_figures.py` |

全量测试（`.venv` 环境 `python -m pytest -q`）：**58 passed, 1 skipped**（2026-08-18）。

### 3.2 “无臆断”的判定边界

- **已做实并归档**：开放数据装配、空间 CV、常量基线对账、Jaccard 阶梯、自适应消融、Sandy 负对照、`PFI_h` 情景循环（平坦响应如实报告）、OOF 判别指标。
- **显式未做（文中以“待补充/尚未建立/未主张”标注，不填数字）**：观测事件降雨（非合成）、citywide 范围、FloodNet 留出传感器验证、雷达降雨、PFIb 复现、降雨条件判别。
- **禁止的推断**（已从文中移除或降级）：不得把“扩展窗口 accuracy 超过基线”写成“学到了可迁移判别信息”；不得把“两个窗口正类占比不同”写成“已证明小窗口是空间伪象”；不得把“R² 0.525”写成“证明样本规模/覆盖是 R² 近零的因果原因”。

### 3.3 快照完整性与外部可访问性

- **不可变发布（immutable release）：** 论文发布版本在仓库中以**注释标签 `paper-v1`** 固化；标签即不可变引用，指向最终论文文本（R21）及生成全部论文输出的确切 commit，而非移动中的 `master` 分支。**标签 `paper-v1` → commit `b49379c5361f82587439afcfba13be33bb0b5910`**（`git rev-list -n 1 paper-v1` 可复核）；GitHub 上同一标签对同一 commit 可见。R18–R21 仅为文字/逻辑/图注/表述润色（全部数字与结果未变），故标签前移至最终 commit 而不影响复现性。
- **原始数据可溯源：** 不强制再分发全部原始栅格/矢量（体积与许可考虑），但 `data/raw/*/DOWNLOAD_MANIFEST.json` 已逐层记录 **来源 URL + 检索日期 + 许可/状态**；`data/raw/DATA_SOURCES.md` 记录 observed / synthetic / fixture 三态约定。
- **审计文档定位：** `docs/paper/audit.md` 作为**支撑性可复现文档**（supplementary reproducibility doc），不替代正文 Methods / Results；审稿人可脱离本文档判断论文本身，本文档仅用于对账与复算。

---

## 4. 审查人复现步骤（如何逐条验证）

```powershell
# 0. 环境
pip install -e ".[raster]"

# 1. 下载扩展窗口原始数据（若未下载）
python scripts\download_nyc_data.py --bbox-profile manhattan_expanded --out data\raw\nyc_expanded --dem-size 900,1200

# 2. 复算扩展窗口主表（重装配 + 重训练 + 常量基线 + OOF 判别指标）
python scripts\run_expanded_study.py
# → 产出 outputs/expanded_primary_table.json、classification_baselines_expanded.{json,csv}
#    models/nyc_expanded/spatial_cv_folds.csv、spatial_cv_oof_predictions.csv

# 3. 复算小窗口基线
python scripts\compute_classification_baselines.py
# → 产出 outputs/classification_baselines.{json,csv}

# 4. 全量测试
python -m pytest -q

# 5. 数字对账：把 manuscript.md/report.md 中每个数字与 §2 所列字段逐一比对
```

**判定：** 若 `run_expanded_study.py` 与 `compute_classification_baselines.py` 的输出字段与手稿数字在四舍五入后一致，则结果可复现、真实、完整。

---

## 5. 尚未完成项（待补充）——诚实清单

| 项 | 状态 | 文中表述 |
|----|------|----------|
| 观测事件降雨（非合成） | 待补充 | 当前 `event_rainfall.tif` 为合成常数；文中明示未演示降雨条件判别 |
| `PFI_h(c,r)` 情景非平坦 | 待补充 | 当前 within-cell range = 0，如实报告 |
| citywide 范围 | 待补充 | 两个试点均为曼哈顿子集，未主张全市技能 |
| FloodNet 留出验证 | 待补充 | 传感器层未接入（当前无可用的 FloodNet 观测） |
| 雷达降雨 / PFIb 复现 | 明确不做 | 文中以“不主张/不复现”显式排除 |

---

## 6. 自查结论

1. **真实**：所有量化结论均由本仓库代码在本机 `data/raw/`（开放数据 + 明确标注的合成降雨）上计算，来源可逐层溯源到 `DOWNLOAD_MANIFEST.json` 与 `DATA_SOURCES.md`；不使用 PFIb / 保险索赔，不抄录 Svellingen 等文献的 Jaccard 0.14 / 效率数字。
2. **准确**：手稿/报告每个数字均可映射到 `outputs/*.json`、`models/*/*.csv` 的具体字段，且逐条对账一致（§2）。R11 的“always-positive vs majority”混用缺陷已修复并重算归档。
3. **完整**：代码路径完整、测试通过（58 passed, 1 skipped）、seed 固定可复现；未完成项均以“待补充/尚未建立”显式标注，**无“做一半臆断一半”**。

---

## 7. 方法学表述与代码一致性核查（2026-08-19 W3）

第 3 轮 ChatGPT 评审要求把“我们自己的方法”写得更清楚、更详细，并核对数据真实性。**所有新增表述均已逐条与源码比对，不写入任何代码未实现的细节。** 核查记录：

| 手稿位置 | 代码依据 | 结论 |
|----------|----------|------|
| §3.3 模型超参 | `src/pluvial_flood_risk/estimators.py`：`GradientBoostingClassifier/Regressor(n_estimators=80, max_depth=4, learning_rate=0.08, random_state=42)` + `StandardScaler`；`LogisticRegression(max_iter=500, random_state=42)`（默认 C=1.0 / L2 / lbfgs） | 已写入超参与 sklearn 1.8 默认；版本来自 `models/nyc_smoke/run_metadata.json`（sklearn 1.8.0，h3 4.4.2） |
| §3.4 AP 定义 | `metrics.py` / `spatial_cv.py` 使用 `sklearn.metrics.average_precision_score` | 改为“recall-weighted mean of precision”，不再写作“PR-AUC 面积” |
| §3.6 自适应加密 | `pipeline.py nyc_smoke_test` + `adaptive.py` + `outputs/adaptive_vs_fixed_ablation.csv`：`score_col=PFI_h`、`proba_col=flood_probability`、`score_quantile=0.8`、`uncertainty_min=0.7`（即 p∈[0.35,0.65]）、`expand_k=1`；79/141 → 3933 vs 6909；**未重训练 R11**；**未计算 hotspot recall** | 补不确定性准则 + 一环邻域扩展；删除“hotspot recall”（代码未产出该指标）；明确“仅改变表征、不重训 R11” |
| §3.8 / §4.5 负对照 | `negative_control.py` + `outputs/negative_control.json`：`score_col = flood_risk`（**观测标签分**），非模型预测 | 改为“观测标签分”表述，不再误写“预测” |
| §3.1/§3.2 特征与度量 | `raster.py`（D8 单流、`np.gradient` 坡度）、`features.py`（haversine 距离、`h3.cell_area`）、`crs_warp.py`（EPSG:4326） | 已补：面积 = H3 原生六边形面积、距离 = 大圆 haversine、地形导数 = 栅格计算后分区平均 |
| §3.5/§4.2 尺度损失饱和 | `rollups.py` + `outputs/jaccard_by_resolution.csv`：`fine_hotspot_threshold=1.0`，`n_hotspot_fine=571/991`（开放标签分饱和于最大值，0.9 分位与最大值重合） | 已如实披露“0.9 分位因分数饱和而退化” |

**数据真实性结论：** `models/nyc_smoke/run_metadata.json → data_provenance="observed"`；`outputs/negative_control.json → assembly_mode="opendata"`；`data/raw/nyc/` 无 `SCHEMA_FIXTURE.txt` 标记且含 `DOWNLOAD_MANIFEST.json`（逐层记录 USGS 3DEP / Esri NLCD / NHDPlus HR / NYC DEP / NYC 311 / USGS Ida HWM / FEMA Sandy 的来源、n_features 与状态）。唯一合成项为 `event_rainfall.tif`（常数 75 mm/h，已显式声明）。故静态特征与标签均为真实开放数据，仅降雨条件为合成常数——与正文声明一致。

---

## 8. 图表补全与数值一致性核查（2026-08-19 W6）

用户要求对照参考论文（Svellingen et al. 2026 IJDRR）的图表类型：**先有直观空间结果图，再有多分辨率/高阶统计图；表格要足够**。本轮新增 **Fig 2（空间结果图）** 与 **Fig 5（分辨率效应图）**，并把手稿从"4 图 0 表"升级为"**6 图 6 表**"。全部数值再次与磁盘 live 文件对账，逐条记录如下。

### 8.1 参考论文图表类型清单（对照基准）

| 参考论文图 | 类型 | 本项目对应 |
|-----------|------|-----------|
| Fig 1 概念工作流 | 流程图 | **Fig 1** workflow_schematic ✓ |
| Fig 2 H3 层级/分辨率/分类色标 | 概念多面板 | 以 Fig 1 + Fig 5 覆盖（不复制其 5 级色标阈值，避免 PFIb 校准等同） |
| Fig 3 PFI_b→PFI_h 转换 | 空间图 | **Fig 2** 三面板空间结果图 ✓ |
| Fig 4 多分辨率空间图 | 空间图 | **Fig 2**（同支撑三面板；本工作数据为 R9 支撑，不做 R6/R8/R10/R13 伪多分辨率） |
| Fig 5a 分辨率分布 | 统计图（violin） | **Fig 5a** ✓ |
| Fig 5b Jaccard 持久性矩阵 | 统计图（heatmap） | **Fig 5b** ✓ |
| Fig 6 流域 vs H3 对比 | 空间对比图 | **未做**：需 HUC-12 子流域多边形，项目无此数据；以 Fig 2 的空间结果图覆盖"空间直观图"类型 |

### 8.2 新增图的数据来源与数值复核

| 图 | 数据文件 | 复核项 | 结果 |
|----|----------|--------|------|
| Fig 2a 观测 | `data/processed/nyc_h3_cells.parquet` | median=1.0, mean=0.605, ≥0.8 共 84/141 | 脚本重算一致 |
| Fig 2b 留出概率 | `models/nyc_smoke/spatial_cv_oof_predictions.csv` | mean=0.798；pooled ROC-AUC=0.683、AP=0.861 与手稿一致 | `sklearn.metrics` 重算一致 |
| Fig 2c PFI_h | `outputs/pfi_h_scenarios.parquet`（ida_like） | mean=0.803；与 §4.5 四情景均值 0.8029 一致；面板（c）仅展示一个情景，正文说明全情景不变 | 一致 |
| Fig 2 相关性 | 同上两两 Pearson | observed~oof=0.245, observed~pfi=0.468, oof~pfi=0.509 | 脚本重算一致；正文如实写入 |
| Fig 5a 小提琴 | `data/processed/nyc_h3_cells_r10_labels.parquet`（991 R10）→ `h3.cell_to_parent` mean 上卷 R9(160)/R8(31) | 单元数与 `jaccard_by_resolution.csv` 的 n_fine/n_coarse 一致 | 一致 |
| Fig 5b 热力矩阵 | 同上 + q=0.9 分位 | J(R10,R9)=0.977、J(R10,R8)=0.167 与阶梯 mean 行一致；新增 J(R9,R8)=0.167 | 脚本重算一致 |

### 8.3 新增表的数据来源

| 表 | 数据文件 | 说明 |
|----|----------|------|
| 表 1 数据层 | `data/raw/nyc/DOWNLOAD_MANIFEST.json` | 逐层来源/形态/角色，无编造 |
| 表 2 模型规格 | `src/pluvial_flood_risk/estimators.py` | 与 §3.3 一致 |
| 表 3 空间 CV 汇总 | `models/nyc_smoke/spatial_cv_folds.csv`、`outputs/expanded_primary_table.json`、`outputs/classification_baselines*.json` | 两试点同构；SD 为 ddof=0 |
| 表 4 尺度损失阶梯 | `outputs/jaccard_by_resolution.csv` | 6 行逐值抄录 |
| 表 5 自适应单元数 | `outputs/adaptive_vs_fixed_ablation.csv` | 141/3933/6909、27.9×、56.9% |
| 表 6 Sandy 负对照 | `outputs/negative_control.json` | 逐字段抄录 |

### 8.4 手稿一致性检查（W6 编辑后）

- 图号引用重排：Fig 1 工作流 / Fig 2 空间结果图 / Fig 3 空间 CV / Fig 4 Jaccard 阶梯 / Fig 5 分辨率效应 / Fig 6 自适应消融；正文 `Fig. N` 引用逐一 grep 核对，无残留旧编号（Fig 2→3、3→4、4→6 已全部更新）。
- `scripts/build_manuscript_html.py` 的 `FIGURES` 锚点已更新为 6 图；`manuscript.html` 中 6 个 `<figure id="fig-N">` 顺序为 1→6，与手稿顺序一致。
- 结果小节重排：§4.1 空间模式（新）→ §4.2 空间 CV → §4.3 尺度损失 → §4.4 自适应 → §4.5 降雨情景 → §4.6 Sandy → §4.7 扩展试点。
- 测试门禁：`pytest` 58 passed, 1 skipped；`figures.py` 无 lint 错误。

### 8.5 ChatGPT W6 评审反馈与修复记录（2026-08-19，第 6 轮协作）

**评审方式**：通过 Cursor 内置浏览器向 ChatGPT 注入 5 个附件（manuscript.md、audit.md、figures.py、spatial_maps.png、resolution_effects.png），自动发送 6 个评审问题并抓取回复（存档：`artifacts/chatgpt_reply_W6.md`）。ChatGPT 逐张打开并检查了两张新 PNG；文本文件与 GitHub raw 因会话内不可读，其"逐句 caption / §4.1 精确数值"部分基于 W5 已签核文本与变更摘要判断。

**关键澄清（关于 Fig 2 面板 (a)）**：ChatGPT 提示"面板 (a) 是 flood_class 还是 flood_risk，必须与实际列名二选一"。核查 `data/processed/nyc_h3_cells.parquet` 的 `flood_risk` 列：**连续浮点，双峰构造**（0.0×28、中间连续值×29、1.0×84；min=0、median=1.0、mean=0.605、≥0.8 共 84/141）。因此面板 (a) 的连续 0–1 色标是**正确**的；此前给 ChatGPT 的变更摘要误写为"二元化 0/1"，本轮已在 `report.md` 表述中更正为"双峰构造"。

**MUST-FIX 8 项逐条落实情况**：

| # | ChatGPT MUST-FIX | 落实 |
|---|------------------|------|
| 1 | 确认 panel (a) 变量身份；二元数据不能标连续 | `flood_risk` 为连续双峰，标题 `Observed open-label risk` 保留（正确）；报告中"二元化"误述已更正 |
| 2 | `Deployed PFI_h(c,r)` → `Full-fit / Fitted`，避免 operational-deployment 含义 | `figures.py` panel (c) 标题改为 `Full-fit PFI_h(c, r)`；手稿 §4.1/§4.5 的 Methods 自适应段、Discussion、Fig 2 caption 全部由 deployed→full-fit 统一 |
| 3 | Fig 2 caption 注明 panel (c) 实际降雨情景 r 且非 OOF 验证 | caption 已注明 "shown at the Ida-like rainfall condition r = 75 mm/h"（已有）+ 新增 "Panel (c) shows the full-fit model output and is not an out-of-fold validation map." |
| 4 | caption 用 (a)/(b)/(c) 则图内须加面板标签 | `plot_spatial_maps` 三面板与 `plot_resolution_effects` 双面板均加粗体 (a)/(b)/(c) 标签 |
| 5 | Fig 5(b) 深色单元黑字→白字 | 热力矩阵按值动态着色：v≥0.6 白字、其余黑字（1.000/0.977 现为白字） |
| 6 | Fig 5 caption 说明 R10/R9/R8 属 label 诊断足迹，非 141 监督表 | caption 新增 "These diagnostics use the R10 label-assembly footprint (991 R10 cells) and its R9 and R8 parents; they are not the 141-cell supervised modelling table used in Sections 4.1 and 4.2." |
| 7 | Table 3 加 ddof=0 SD footnote | 表下新增 Note："SD denotes the population standard deviation across the five held-out folds (ddof = 0); the fold-mean values in the first four rows are arithmetic means of the per-fold metrics." |
| 8 | §4.1 报告 full-fit PFI 相关性时加"描述性、非验证"说明 | §4.1 新增 "These correlations are descriptive measures of spatial concordance between the assembled surfaces; predictive performance is evaluated from the out-of-fold metrics reported in Section 4.2." |

**Optional 采纳情况**：

| # | ChatGPT Optional | 落实 |
|---|------------------|------|
| 1 | panel (a) 保持 viridis 与 0–1 线性色标 | 保留（未改） |
| 2 | DEM/水系背景保留 | 保留（未改） |
| 3 | Fig 5(a) 小提琴叠加原始点（尤其 R8 n=31） | 已加：三组低透明度抖动散点（seed 20260819） |
| 4 | Fig 5(b) colorbar 加标签 Jaccard similarity | 已加 |
| 5 | Fig 5 caption 说明 0.167 为实证结果非方法强制 | caption 新增 "The identical 0.167 similarities involving R8 are an empirical result of the realised hotspot sets, not a constraint of the method." |
| 6 | 不加 R6/R7 | 采纳，未加 |
| 7 | Fig 5 标题 persistence→cross-resolution similarity | 图内标题与手稿 §4.3/caption 均改为 "Cross-resolution hotspot Jaccard similarity" |
| 8 | §4.3 用一句区分 Fig 4 与 Fig 5 | 已加 "Fig. 4 therefore examines sensitivity to the aggregation operator, whereas Fig. 5 holds mean aggregation fixed to isolate resolution-dependent changes in score distribution and hotspot membership." |

**新增图是否强化主线（ChatGPT 结论）**：Fig 2 明显强化（把观测→留出→全拟合放在完全相同 H3 support 上，直接可视化 "the grid is the common support"）；Fig 5 有价值但需与 Fig 4 明确分工（本轮已落实分工句）。**两图非单纯增加数量。**

**本轮统计量复核（§4.1）**：n=141；observed min/med/mean/q75/max = 0/1.0/0.6051/1.0/1.0；≥0.8 共 84；OOF mean=0.7983；PFI mean=0.8029；Pearson obs~oof=0.245、obs~pfi=0.468、oof~pfi=0.509——脚本重算全部与正文一致。

**ChatGPT 未能独立复核项（诚实记录）**：§4.1 的精确统计量与 caption 逐句文本，因其会话内未挂载 manuscript.md/数据文件。已在下一轮准备把 `spatial_cv_oof_predictions.csv` 等数据文件一并注入供其复核。

### 8.6 ChatGPT W7 复核与修复记录（2026-08-19，第 7 轮协作）

**评审方式**：向 ChatGPT 注入 8 个文件（manuscript.md / audit.md / figures.py / spatial_cv_oof_predictions.csv / nyc_h3_cells.parquet / pfi_h_scenarios.parquet / spatial_maps.png / resolution_effects.png），请求逐条验证 W6 修复并**用注入数据独立重算 §4.1 统计量**。回复存档：`artifacts/chatgpt_reply_W7.md`。

**W6 修复复核结论**：W6 的 8 个 MUST-FIX + 8 个 optional **全部正确落实**（ChatGPT 逐条确认代码与 PNG）。

**§4.1 独立重算（ChatGPT 直接从注入的 3 个数据文件重新读取/join）**：

| 量 | ChatGPT 重算 | 项目/手稿 |
|----|-------------|-----------|
| n | 141 | 141 ✓ |
| observed min / median / mean | 0 / 1.000 / 0.605075 | 0 / 1.0 / 0.605 ✓ |
| observed ≥ 0.8 | 84 / 141 | 84 / 141 ✓ |
| observed exactly 0 / 1 | 28 / 84 | 28 / 84 ✓ |
| OOF probability mean | 0.798305 | 0.798 ✓ |
| Ida-like full-fit PFI mean | 0.802888 | 0.803 ✓ |
| Pearson obs~OOF / obs~PFI / OOF~PFI | 0.244801 / 0.467873 / 0.508675 | 0.245 / 0.468 / 0.509 ✓ |

全部一致。手稿 §4.1 只打印 OOF~PFI r=0.51，正文与重算一致。

**W7 新 MUST-FIX 4 项落实情况**：

| # | 项 | 落实 |
|---|----|------|
| 1 | §3.5 删除对 Fig. 5 的提前编号引用，恢复 first-mention 1→6 | 已删：改为 "The same diagnostics are additionally summarised through score distributions across resolutions and a pairwise hotspot-similarity matrix."；grep 复核首次出现顺序为 Fig.1(§3.1)→2(§4.1)→3(§4.2)→4(§4.3)→5(§4.3)→6(§4.4) |
| 2 | §4.1 "These correlations" → "This correlation" | 已改（正文只报告一个 Pearson r=0.51） |
| 3 | §4.1 "any positive evidence…lifts the score to a high value" 过强（真实含 29 个 0–1 中间值） | 已改为 "positive evidence yields either a fractional polygon-overlap score or a point-presence score of 1"，与 `labels.py` 构造（面积分数 / 点存在记 1）一致 |
| 4 | Fig. 5(b) "(b)" 标签黑字落在深蓝 1.000 cell 内 | 已改为白字 `color="white"` |

**W7 optional 落实情况**：

| # | 项 | 落实 |
|---|----|------|
| 1 | Fig. 1 caption 拆超长首句、passed to diagnostics → diagnostics include | 已拆句改写 |
| 2 | Fig. 2 caption 将 "not an OOF validation map" 压入 panel (c)；Ida-like → synthetic Ida-like | 已改："…shown at a synthetic Ida-like rainfall condition r = 75 mm/h and not an out-of-fold prediction…" |
| 3 | Fig. 5 caption 两句 defensive 改正向 factual | 已改："The R10 label-assembly footprint contains 991 cells and aggregates to 160 R9 and 31 R8 parents, distinct from the 141-cell R9 supervised modelling table…"；"For the realised hotspot sets, both comparisons involving R8 yield Jaccard similarity 0.167." |
| 4 | Fig. 5(a) 说明 violin 内部 mean/extrema | 已加 "internal bars mark the mean and extrema" |
| 5 | Fig. 2 PFI_h 用 mathtext 与 Fig. 1 统一 | 已改：panel (c) 标题 `Full-fit $\mathrm{PFI}_h(c,r)$`、colorbar `$\mathrm{PFI}_h$` |
| 6 | Table 3 caption 与 Note 的 ddof=0 去重 | 已删 caption 中的 "(ddof = 0)"，仅保留表下 Note 作为正式 statistical convention |

**W8+ 方向（ChatGPT 建议，下一轮执行）**：① 全文 defensive prose 最后一次 sweep（not/do not/are not 密集段落改正向 factual）；② 最终 PDF 版面审阅（6 图 6 表在投稿页宽下的版式）；③ submission-package consistency（CRediT、Highlights、AI declaration、paper-v1 tag/commit、figure PDF 与编号一一对应）。

### 8.7 W8 落实记录（2026-08-19）

**ChatGPT W8 判定**：科学内容与图表一致性 **sign-off**；剩余 3 个投稿前 blocking/production 项 + Highlights 建议。已按下列条目落实，除 CRediT 因作者信息待用户提供而保留占位。

**A. Defensive prose 最后一次 sweep（ChatGPT 逐条给出句子级最小替换）**：

| 优先级 | 位置 | 落实 |
|---|----|------|
| 高 | Abstract | "evaluated without overstating performance" → "evaluated with explicit control for spatial dependence" |
| 高 | §3.3 | "never reported without a class-prevalence comparison" → "reported alongside these constant classifiers to provide a class-prevalence reference" |
| 高 | §3.4 | "Random independent splits … not primary" → "H3-block spatial cross-validation is the primary evaluation; random independent splits are retained as diagnostic comparisons" |
| 高 | §4.1 | "tracks the cross-validated surface closely (r = 0.51)" → "shows moderate spatial concordance … (Pearson r = 0.51)" |
| 高 | §4.1 | "maps are presented for visual inspection … only; they carry no quantitative claim" → "The maps provide a qualitative comparison of the assembled surfaces; quantitative predictive performance is reported in Section 4.2" |
| 高 | §4.4 | "statements concern cell counts only; … are not reported" → "This ablation measures representation size by cell count; runtime, memory use, and city-scale computational cost are outside the reported metrics" |
| 高 | §5.1 | "closely reproduces the cross-validated surface; … not an additional validation" → "shows moderate spatial concordance … Validation is based on the out-of-fold metrics" |
| 高 | §5.3 | "This is what distinguishes the framework…" → "Using the same hierarchy for these four operations extends H3 from a post-prediction visualisation layer to the learning and evaluation architecture" |
| 高 | §5.3 | "not demonstrated … noted rather than resolved" → "block-size sensitivity remains a limitation"（保留证据边界） |
| 高 | §5.4 结尾 | "must not displace" → "Primary performance claims are based on spatial cross-validation; random-split accuracy is retained as a diagnostic comparison" |
| 中 | §4.7 | "not as citywide skill" → "provides a robustness check within Manhattan; citywide generalisation remains unevaluated" |
| 中 | §5.1 | "higher value … does not imply stronger classification" → "interpreted relative to its higher prevalence baseline" |
| 中 | §5.4-1 | "neither of which is citywide" → "both of which are sub-city Manhattan extents" |
| 中 | §5.4-4 | "ingestion of gauge or radar event rainfall is not implemented" → "uses constant synthetic rainfall rather than event-specific gauge or radar rainfall" |
| 中 | §5.4-8 | "not as citywide predictive skill" → "interpreted within their respective pilot extents" |
| 中 | Conclusions | "they do not establish citywide operational skill" → "the evidence is limited to the two Manhattan pilot extents" |
| 低 | §4.5 | "A non-zero response requires…" → "Evaluating rainfall responsiveness requires observed event rainfall with variation across intensities and model retraining" |

保留的必需否定（科学诚实）：§3.5 "not a reproduction"、§3.7 "not SHAP/permutation/PFIb"、§3.8 Sandy "never a training label"、Fig.1 "never a training label"、Fig.2 full-fit vs OOF、constant synthetic rainfall 证据边界、§5.2 "conceptual rather than numerical"。**所有数字与结论未变**。

**B. 版面重渲染（按投稿目标物理宽度）**：

| 图 | 源码 figsize 旧 → 新 | 目标宽度 | 落实 |
|----|----------------------|---------|------|
| Fig. 1 workflow | 11.2×6.4 → 7.48×4.27 in | 190 mm 双栏 | 内部 box 文本按更紧凑布局重排（3–4 行/box），字号 8 pt（≥7 pt 达标） |
| Fig. 2 spatial maps | 12.0×4.4 → 7.48×2.74 in | 190 mm 双栏 | 三面板保持双栏；colorbar tick 8 pt / label 9 pt |
| Fig. 3 spatial CV | 6.4×3.4 → 5.51×2.93 in | 140 mm 1.5 栏 | 达标 |
| Fig. 4 Jaccard ladder | 9.2×3.6 → 7.48×2.93 in | 190 mm 双栏 | 达标 |
| Fig. 5 resolution effects | 9.6×3.8 → 7.48×2.96 in | 190 mm 双栏 | (b) 白字、annotations 可读 |
| Fig. 6 adaptive | 6.0×3.4 → 5.51×3.12 in | 140 mm 1.5 栏 | 达标 |

PNG+PDF 均已按新尺寸重生成到 `docs/paper/figures/`。图号/正文 first-mention 顺序 1→6、文件名对应关系此前已核实一致。

**C. submission-package 一致性**：

| 组件 | 状态 | 落实 |
|------|------|------|
| Highlights | 已补 | 新增 "## Highlights" 5 条候选（各 ≤85 字符，无缩写），置于标题与 Abstract 之间 |
| AI declaration | 标题已改 | "Declaration of generative AI and AI-assisted technologies in the manuscript preparation process"（Elsevier 当前推荐格式）；正文表述不变 |
| Data availability | 已改 | 指向新 tag `submission-v1`；版本精确化：scikit-learn 1.8.0 / H3 4.4.2；commit 由 audit 记录 |
| References [11]–[17] | 已对齐 | 从"机构主页 n.d."改为实际数据服务 URL + "accessed August 2026"：3DEP ImageServer、NLCD 年度分数不透水面 ImageServer、NHDPlus HR MapServer、DEP 311 数据端点、USGS Ida HWM **DOI 10.5066/P9OMBJPQ**、FEMA Sandy uyj8-7rv5 端点 |
| CRediT | **仍为 blocking** | 用户选择保留 [待补充] 占位，提交前需补作者姓名与角色 |

**D. W7 回归确认**：ChatGPT 逐项复核 W7 的 4 MUST-FIX + 6 optional 全部正确落地，无科学/数值回归（详见其 W8 回复 §D）。

**W8 遗留（投稿前）**：① CRediT 作者角色待用户提供；② 建 `submission-v1` tag（推送后执行，见 8.8）；③ Highlights 可选再核对；④ `Fig1_workflow.pdf … Fig6_adaptive.pdf` 上传别名建议保留。

### 8.8 W8 提交与 tag 记录（2026-08-19）

`submission-v1` tag 已在 W8 最终 commit 上创建并推送（`git rev-list -n 1 submission-v1` 可复核），manuscript Data availability 声明指向该 tag。
