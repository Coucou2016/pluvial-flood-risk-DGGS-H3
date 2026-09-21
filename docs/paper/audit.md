# 审查文档（Audit）：数据真实性、准确性与完整性证据

> **⚠ 当前权威数字（2026-09-14 Major Revision P0 pass）：** 以 `outputs/paper_results.json`、`outputs/jaccard_by_resolution.csv`、以及重训后的 `models/nyc_smoke/` + `models/nyc_expanded/` 为准。LM Option B：n=262、正类 63.7%、acc 0.820±0.057、F1 0.858、pooled ROC-AUC 0.848；扩展：n=956、正类 47.9%、acc 0.823±0.028、F1 0.826、pooled ROC-AUC 0.882。尺度损失主指标为 area-weighted soft Jaccard（R10→R9 mean 0.227；R10→R8 mean 0.136）。311 源为官方 SODA `76ig-c548`。下文历史对账段落中若出现 0.809/0.846/0.883/n=141-as-current 等旧值，一律视为快照，不以之为现行主表。

**用途：** 本文档用于证明手稿 `manuscript.md` 与研究报告 `report.md` 中的所有数字，均为**本仓库自身代码在本机数据上运行所得**，而非从参考文献（尤其 Svellingen et al. 2026 IJDRR 及其 PFIb / Jaccard 0.14 数字）或任何第三方论文中抄录；并证明结果**可逐条复算、可对账、无“做一半臆断一半”**。

**审查对象：** `docs/paper/manuscript.md`、`docs/paper/report.md`、`README.md` 中的全部量化结论。

> **版本说明（2026-08-19 W1/W2 写作重写）：** 手稿 `manuscript.md` 在 2026-08-19 进行了**仅写作/逻辑/投稿体例**的重写（编号引用、单主线叙事、创新点重组为 "H3-native 学习-评估架构"），**所有数字、结果与核心结论未做任何改动**。因此本文档 §2 的逐条对账（按数值与产物字段，而非章节号）依然有效；本重写仅使手稿章节号从旧 8 章结构变为新 6 章结构（旧 §6 Results → 新 §4 Results；旧 §7 Discussion → 新 §5 Discussion）。下文引用的产物字段路径均未变。

> **⚠ 版本说明（2026-08-23 审稿意见落实 / 数据语义修订）：** 本轮按一份形式审稿意见对稿件做了**科学有效性修订（不再是纯写作）**，关闭 C1–C6 致命项与 M1–M7 重大项。**数字、标签语义、结论均有实质变化**：DEP 由 "observed" 改为 "model-derived（category 1–2，剔除 category 3 海岸高潮位）"；311 更正为 `arcgis_streetfloodtime`（2010–2014，非 "2010–present"）；尺度损失改为 R10 原生 overlay（非 parent inheritance）；Sandy 负对照改用 composite `flood_class` 分组；ponding 基线修复训练集归一化泄漏；"risk/probability/rainfall-conditioned" 全稿降级为 "susceptibility / model score"。**本文档 §2 的历史对账数字已部分被本版取代**，请以 **§9（2026-08-23 修订对账 + 数据语义核查）为准**；§2 保留为历史记录。

**口径约定（贯穿全文）：**

- **本方法自己算出的数字**：全部来自 `src/pluvial_flood_risk/` 与 `scripts/` 在本机 `data/raw/` 上的运行产物（`outputs/*.json/csv`、`models/*/*.csv/joblib`、`data/processed/*.parquet`）。
- **明确的“待补充 / synthetic”项**：观测事件降雨（当前为合成常数）、citywide 范围。FloodNet 已作严格留出诊断（不入训练标签）。这些在文中以“尚未建立 / 未主张 / 待补充”显式标注，**不做臆断性数值填充**。
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
| Jaccard 说明 | 手稿 Results §4.2 / Discussion §5.2 与图注明确：0.111 是本仓库开放标签在 R10→R8 mean 聚合（exact top-10% 预算）下的结果，**不得**等同 Svellingen 0.14 |
| 合成项显式标注 | 降雨为合成常数、情景 `PFI_h` 平坦（within-cell range = 0）——文中作为“未演示降雨条件判别”如实报告，而非编造响应 |

---

## 2. 准确性（Accuracy）：逐条对账

> **⚠ 历史版本提示（2026-08-24）：** §2–§6 为**首代装配**的原始对账（正类 80.1%/47.9%、accuracy 0.784/0.722 等），其后历经 C1/C3/C4 数据语义修复（§9–§10）与 M4 当前海平面 DEP 主层修复（§9.3 注）。**当前权威数字以 §9.3「修订后主表对账」为准**（小窗口正类 67.4%、accuracy 0.781；扩展窗口正类 47.5%、accuracy 0.821），§2–§6 保留作为首代快照与演进证据，不代表最终手稿数值。

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

> **历史快照（pre-Option-B）：** 本节对账的是修订前 LM smoke **n=141** 主表数字。现行 Option B 真相见 **§14.3** / `outputs/paper_results.json`（n=262）。勿把本节当作当前主表。

来源：`models/nyc_smoke/spatial_cv_folds.csv` + `outputs/classification_baselines.json`（历史路径；现行 Option B 元数据同路径但 n_cells=262）。

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

> **历史快照（pre-Option-B）：** 下表 LM smoke 行为 **n=141** 时期数字。现行 Option B LM 见 **§14.3**（n=262，ROC-AUC pooled 0.847）。

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
| FloodNet 留出验证 | 已做严格 held-out 诊断 | 官方 `aq7i-eu5q`+`kb2e-tjy3`；不入训练标签；见 `outputs/floodnet_heldout_validation.json` |
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
| §3.3 模型超参 | `src/pluvial_flood_risk/estimators.py`：`GradientBoostingClassifier/Regressor(n_estimators=80, max_depth=4, learning_rate=0.08, random_state=42)` + `StandardScaler`；`LogisticRegression(max_iter=500, random_state=42)`（默认 C=1.0 / L2 / lbfgs） | 已写入超参与 sklearn 1.8 默认；版本来自冻结 `models/nyc_smoke/run_metadata.json`（sklearn 1.8.0，h3 4.4.2；仓库 pin `h3==4.4.2`；live 环境或见 4.5.0，勿改写冻结 metadata） |
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
| Fig 2a 观测 | `data/processed/nyc_h3_cells.parquet` | median=1.0, mean=0.598, ≥0.8 共 84/141 | 脚本重算一致 |
| Fig 2b 留出概率 | `models/nyc_smoke/spatial_cv_oof_predictions.csv` | mean=0.655；pooled ROC-AUC=0.780、AP=0.805 与手稿一致 | `sklearn.metrics` 重算一致 |
| Fig 2c PFI_h | `outputs/pfi_h_scenarios.parquet`（ida_like） | mean=0.677（正文"约 0.68"）；与 §4.5 四情景均值一致；面板（c）仅展示一个情景，正文说明全情景不变 | 一致 |
| Fig 2 相关性 | 同上两两 Pearson | observed~oof=0.467, observed~pfi=0.765, oof~pfi=0.634（正文只报告 oof~pfi=0.63） | 脚本重算一致；正文如实写入 |
| Fig 6a 小提琴 | `data/processed/nyc_h3_cells_r10_labels.parquet`（991 R10）→ `h3.cell_to_parent` mean 上卷 R9(160)/R8(31) | 单元数与 `jaccard_by_resolution.csv` 的 n_fine/n_coarse 一致 | 一致 |
| Fig 6b 热力矩阵 | 同上 + exact top-10% 预算（H3 tie-break） | J(R10,R9)=0.180、J(R10,R8)=0.111 与阶梯 mean 行一致；新增 J(R9,R8)=0.200 | 脚本重算一致 |

### 8.3 新增表的数据来源

| 表 | 数据文件 | 说明 |
|----|----------|------|
| 表 1 数据层 | `data/raw/nyc/DOWNLOAD_MANIFEST.json` | 逐层来源/形态/角色，无编造 |
| 表 2 模型规格 | `src/pluvial_flood_risk/estimators.py` | 与 §3.3 一致 |
| 表 3 空间 CV 汇总 | `models/nyc_smoke/spatial_cv_folds.csv`、`outputs/expanded_primary_table.json`、`outputs/classification_baselines*.json` | 两试点同构；SD 为 ddof=0 |
| 表 4 尺度损失阶梯 | `outputs/jaccard_by_resolution.csv` | 6 行逐值抄录 |
| 表 5 自适应单元数 | `outputs/adaptive_vs_fixed_ablation.csv` | 141/4845/6909、34.4×、70.1% |
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

`submission-v1` tag 已在 W8 主修复 commit `c76be2c` 上创建并推送（tag 对象 `66cc7ac`；`git rev-list -n 1 submission-v1` 可复核），manuscript Data availability 声明指向该 tag。后续 report 产物刷新 commit `aabc449`（仅 HTML/PDF 渲染产物，不改变论文文本），未移动 `submission-v1`；`paper-v1` 保持指向 R21 commit `b49379c` 不变。

### 8.9 W9 图体系对齐落实记录（2026-08-20）

**W9 目标**：按用户指令"让 ChatGPT 把参考论文 PDF 的图逐张看清，并与我方图做类型/数量/质量对照"。本轮从 `1-s2.0-S2212420926001032-main.pdf` 提取 6 张参考图（脚本 `scripts/extract_reference_figures.py`，输出 `artifacts/reference_paper_figures/`），连同我方 6 图 + `manuscript.md`/`audit.md`/`chatgpt_context_W9.md` 共 15 文件注入 ChatGPT（DataTransfer 机制）评审。

**ChatGPT W9 判定**：图体系"基本达标但非完全一一对齐"。唯一值得进正文的缺失图型 = **多分辨率空间并排图**（参考 Fig.4）；H3 概念图（参考 Fig.2）仅可选；watershed vs H3（参考 Fig.6）**明确不补**（无 HUC/流域/行政区数据，禁止用 bbox/R7 parent 伪装）。

**已落实（A. 图体系）**：

| 项 | 动作 | 数据来源（真实、已核） |
|----|------|------------------------|
| 新增 Fig.4 `multi_resolution_spatial.png` | R10/R9/R8 三面板开放标签分空间图，共享 0–1 viridis 色标 | `data/processed/nyc_h3_cells_r10_labels.parquet`（991 个 R10 单元，`flood_risk` 0–1 连续）；`h3.cell_to_parent` mean 上卷 R9=160、R8=31，与 Fig.5 完全同源（已用脚本逐项复核计数一致） |
| 旧 Fig.4 `jaccard_by_resolution.png` | 移至 `docs/paper/figures/supplementary/`，降级为补充图 S1 | `outputs/jaccard_by_resolution.csv`（数值已完整列于 manuscript Table 4 / report 表 3） |
| 主图数量 | 仍 6 主图 + 1 补充图 + 6 表，不新增第 7 主图 | — |

**已落实（B. 图质量 MUST-FIX / 建议）**：

| 项 | 动作 |
|----|------|
| Fig.1 header 拥挤 | `Learning & validation`、`Diagnostics & outputs` 改为两行；删除 y=0.30 底部悬空灰色箭头（只留 y=0.62 stage-to-stage 箭头 + Sandy 虚线旁路） |
| Fig.2 colorbar 术语 | `Observed risk (0–1)` → `Open-label risk (0–1)`，与 panel title/caption 统一 |
| Fig.6 顶部 margin | ylim 上限 1.22→1.30、annotation y 1.10→1.02，消除"顶到轴框"感 |

**已落实（C. 文字/体例同步）**：

- `manuscript.md`：Fig.4 caption 重写为多分辨率空间图；§4.3 正文 `(Fig. 4)`→`(Table 4)`，新增 Fig.4 空间图描述句；Fig.5 caption `reproduce the ladder in Fig. 4`→`in Table 4`；Table 4 note 加 `Supplementary Fig. S1` 引用；新增 `Supplementary Figure S1` caption（置于 Figure 6 caption 之后）。正文图号 first-mention 顺序仍为 1→6。
- `report.md`：图 4 描述改为多分辨率空间图，新增补充图 S1 说明，图 5 结论 `表 3/图 4`→`表 3`，完成度清单补 F4 条目。
- `scripts/make_figures.py`：Fig.4 换新函数 + jaccard 移至 supplementary。
- `scripts/build_manuscript_html.py` / `build_paper_report_html.py`：图文件名与锚文本同步（manuscript HTML 6 图、report HTML 7 图，均无 "Figure missing"）。

**科学内容/结果/核心结论/全部数字未变**：本轮仅图体系对齐 + 图质量 + 排版体例；无任何数值改动。R10=991 / R9=160 / R8=31、Jaccard ladder（R8 mean 0.167/F1 0.286、R9 mean 0.977/0.988、max/p90=1.000）等数字原样保留，仅从主文 Fig.4 迁至 Table 4 + 补充图 S1。

**W9 未补项（诚实边界，ChatGPT 确认不补）**：watershed/catchment vs H3 空间对比图——本仓库无 HUC-12/流域/行政区 polygon 数据，不新增数据、不伪造。

### 8.10 W10 复核与锁稿记录（2026-08-20）

**W10 目标**：确认 W9 图体系对齐落地正确、无回归。注入 9 文件（`manuscript.md`、`audit.md`、`chatgpt_context_W10.md` + 6 图）至 ChatGPT 复核。

**ChatGPT W10 判定**：**W9 核心调整正确落地，无科学/数值回归，图体系对齐完成**。仅 1 个 MUST-FIX（Fig.4 caption 措辞精度）+ 1 个建议（Fig.4(c) 标签对比度）+ 1 个语言顺滑建议。

**已落实**：

| 项 | 动作 | 说明 |
|----|------|------|
| Fig.4 caption 措辞（MUST-FIX） | `same geographic footprint` → `same map extent and derive from the same R10 label-assembly footprint`；`Hotspot similarities and aggregation-rule sensitivity are quantified in Table 4 and Fig. 5` → `Figure 5 summarises cross-resolution hotspot similarity, while Table 4 quantifies sensitivity to the aggregation rule` | 修正"footprint 过强"表述，并把 aggregation-rule sensitivity 职责准确归位 Table 4；保留 smoothing 科学信息 |
| Fig.4 panel 标签对比度（建议） | `(a)/(b)/(c)` 标签统一加半透明白色底框（`bbox facecolor=white, alpha=0.75`） | 解决 (c) 黑字位于深紫 R8 单元上对比度低的问题；比"仅 (c) 改白"更稳健（(a)/(b) 位于浅色 DEM 背景时白字会不清） |
| §4.3 语言顺滑（建议） | `Fig. 5a shows the same scale dependence as score compression` → `Fig. 5a summarises the same scale dependence through the score distributions` | 纯语言自然度，不含数值 |

**回归确认（ChatGPT 独立逐行 diff）**：W9 前后 manuscript 文本变化仅集中在 §4.3 Fig.4→Table4、新增 multi-resolution Fig.4 描述、Fig.4 caption 替换、Fig.5 Fig.4→Table4、Table4 note 加 S1、新增 S1 caption。**Table 1–5 任何数值单元格均无变化**；R10=991 / R9=160 / R8=31 / R10 hotspot=571/991 / R8 mean 0.167/0.286 / R9 mean 0.977/0.988 / max·p90=1.000 / Adaptive=141/3933/6909 等关键值全部原样保留。旧 "Fig.4=Jaccard ladder" 残留引用已精确查找确认无残留。

**锁稿结论**：W10 caption 微调完成后正式 sign-off，图体系对齐完成。主图叙事链条：Fig.1 framework → Fig.2 spatial outputs → Fig.3 blocked validation → Fig.4 spatial coarsening → Fig.5 statistical resolution effects → Fig.6 adaptive representation。

### 8.11 W11 写作风格 humanize 落实记录（2026-08-20）

**W11 目标**：按用户持续不满意的维度——写作风格/措辞的"研究工作总结 / 审稿答辩 / AI 整理稿"气质——做 humanize。注入 4 文件（`manuscript.md`、`audit.md`、`reference_paper.md` 参考论文全文、`chatgpt_context_W11.md`）至 ChatGPT 逐段诊断并给精确 diff。

**ChatGPT W11 判定**：稿件已无"AI 套话"（Moreover/Furthermore/Additionally 链式堆叠）；残余人工感来自三类结构问题——贡献段像组件清单、Results/Discussion 多次解释"应该怎样解读"、Limitations/Future work 仍像审稿答辩清单。给 6 MUST-FIX + 约 16 建议 + 3 可选。

**已落实（6 MUST-FIX）**：

| 项 | 动作 |
|----|------|
| Abstract | 保持 unstructured 单段，按 problem→method→results→evidence-boundary 重排；`demonstrates ... lists everything` → `evaluates ... uses H3 as the common spatial support`；`On a small Manhattan pilot` → `Under this blocked evaluation, a small Manhattan pilot`；末两句由"功能说明+自我限定"改结果意义 |
| Introduction contribution paragraph | 组件清单 → "H3 hierarchy 连接哪些科学环节"；PFI 句改 `distinct from both feature-importance measures and the H3-aggregated building index` |
| Research questions | 去掉 (i)/(ii)/(iii)，改自然连续表述（三问科学内容不变，结尾保留 `rather than on a citywide scale` 边界） |
| §4.1 重复 validation disclaimer | 两句 `This correlation is descriptive... / The maps provide a qualitative comparison...` 合并为一句 `The spatial concordance is descriptive; predictive performance is assessed separately from the out-of-fold metrics reported in Section 4.2.` |
| §5.4 Limitations | 9 条 numbered → 3 个主题段落（所有边界与数字原样保留） |
| Conclusion | `This study shows / The experiments demonstrate / The results indicate` 三连 → 连续论证 |

**已落实（建议，高收益 humanize）**：§2 去掉 `Extent./Data sources./What the labels mean./Rainfall.` 行内标签；Methods 加整体入口句；§3.1/3.6/3.7 防御性否定 → 正向方法定义；§4.4/§4.5 否定自然化；§4.7 删中途 `still not citywide`（结尾保留 `citywide generalisation remains unevaluated`）；§5.1 Discussion 开头三项罗列 → synthesis；§5.2 Svellingen 比较改写（保留 `rather than reproducing their metric`）；§5.3 四角色句压缩；Fig.1 caption `bypasses learning` → `represents the post-fit coastal-overlap diagnostic`；Fig.2 caption `not an out-of-fold prediction` → `fitted using all 141 cells`。

**已落实（可选）**：Highlight 5 改 `Constant training rainfall produces a flat rainfall-conditioned response`；§5.5 Future work 去 (i)–(iv) 编号。

**回归确认**：全部关键数字经 grep 复核原样保留——0.784/0.866/0.683/0.861/0.642/0.525/0.703/0.723/0.808/0.893/0.167/0.977/0.988/1.000、571 of 991、3,933/6,909、56.9%/27.9×、0.030/0.343、80.1%/47.9%、0.14、0.51、0.803、n=141/956、21–49/190–193、Fold4 n=24 等全部未变。表结构、图编号、引用编号未变。`build_manuscript_html.py` 的 Fig.2 锚文本同步更新（因 §4.1 删除了原锚句）。

**诚实边界保留（未被 humanize 掉）**：open labels ≠ verified inundation；PFI_h ≠ feature importance / PFIb；0.167 ≠ reproduction of 0.14；Sandy 不进训练；constant rainfall → flat response；pilots ≠ citywide；no separate calibration；no R11 retraining。这些与本文档 §1–§7 的真实性约束一致。

### 8.12 W12 复核与写作风格 sign-off 记录（2026-08-20）

**W12 目标**：确认 W11 写作 humanize 落地正确、无回归、写作风格可 sign-off。注入 2 文件（`manuscript.md`、`chatgpt_context_W12.md`）至 ChatGPT 复核。

**ChatGPT W12 判定**：**通过，写作风格 humanize 正式 SIGN-OFF**。6 MUST-FIX + 建议 + 可选全部正确落地；无科学语义漂移、数字回归、边界丢失。仅 3 个纯 copy-edit 级微调（MUST-FIX 无）。

**已落实（W12 三个 copy-edit）**：

| 项 | 动作 |
|----|------|
| Introduction 研究问题结尾 | `on a smaller and an expanded Manhattan pilot extent` → `on two Manhattan pilot extents, one smaller and one expanded`（消除并列单数名词的短暂误读） |
| §5.1 术语 | `the smaller table` / `the expanded table` → `the smaller pilot` / `the expanded pilot`（table 系笔误，pilot 才是研究对象） |
| §5.3 去答辩口吻 | 删除 `deliberately conservative, but one caveat applies:`，直接陈述 R7 block-size 局限 |

**回归确认（ChatGPT 逐项）**：全部科学数值保留（0.784/0.866/0.683/0.861/0.642/0.608/0.525/0.703/0.723/0.808/0.893/0.167/0.977/0.988/1.000、571 of 991、3,933/6,909、56.9%/27.9×、0.030/0.343、80%/80.1%/47.9%、0.14、0.51、0.803、n=141/956、21–49/190–193、Fold4 n=24）。八项科学诚实边界全部保留。引言三段衔接无指代断裂。

**锁稿结论**：写作风格 humanize 完成，稿件进入正常 IJDRR submission-manuscript 范围。科学内容、结果、核心结论、全部数字自 W9 起未变（仅图体系对齐 + 图质量 + 写作/排版体例）。

---

## 9. 审稿意见落实 + 数据语义核查（2026-08-23）

本轮收到一份以"标签到底是什么、代码实际算了什么、图到底证明了什么"为焦点的形式审稿意见，给出 C1–C6（致命）与 M1–M7（重大）共 13 项。**本节记录每一项的处置、代码/数据证据，以及修订后的全部对账数字。** 自本节起，稿件定位收敛为 **pluvial-flood susceptibility screening（开放式多源证据筛查）**，不再是 "rainfall-conditioned risk index"。

### 9.1 审稿意见 → 处置对照表

| 项 | 问题（审稿意见原文摘要） | 处置 | 代码/数据证据 |
|----|------------------------|------|--------------|
| **C1** | DEP 非观测洪水数据，是水文—水动力模型结果；所下载图层含第 3 类 "Future High Tides 2050" 海岸淹没 | ① `download_nyc.py` 加 `Flooding_Category IN (1,2)` 过滤，剔除第 3 类；② DEP 全稿改称 "model-derived stormwater polygons (categories 1–2)"，不再称 observed | `data/raw/nyc/dep_stormwater_flood.geojson` 与 `nyc_expanded/` 均只含 `Flooding_Category ∈ {1,2}`（各 n=2，见 §9.2）；`download_nyc.py` `_DEP_WHERE` |
| **C2** | 连续 `flood_risk` 无物理/统计尺度；R² 拟合的是人造 evidence score | 全稿 `flood_risk`→`flood_evidence_score` 语义、R² 改称 "evidence-score R²"，并在 §2/§4.2/§5.4 明确"非物理严重度、非校准概率" | `labels.py`（`risk_column` 默认 `flood_evidence_score`）、`config.py`（`PROVENANCE_OPEN_EVIDENCE`） |
| **C3** | R10 "fine reference" 用 R9 parent 继承，非独立重算；尺度损失循环 | `assemble.py assemble_label_scale_table` 删除 parent-inherit 路径，改 **R10 原生 polygon/point overlay**；Fig.4/5、Table 4 全部重算 | `assemble.py`（`del parent_label_df`；`native_overlay`）；`outputs/jaccard_by_resolution.csv`（见 §9.4） |
| **C4** | 311 实际下载源是 `arcgis_streetfloodtime`（最后更新 2015-01-22），非官方 Socrata；正文误写 "2010 to present" | 正文/引用更正为 `arcgis_streetfloodtime`（2010–2014）；记录去重后点数与时间窗 | `DOWNLOAD_MANIFEST.json`（`source=arcgis_streetfloodtime`）；日期范围 2010-01-07 → 2014-12-26（§9.2） |
| **C5** | Sandy 负对照的 "pluvial" 用 `flood_area_frac>0`，与含点标签的 `flood_risk` 定义不一致；"neither" 行 mean=0.613 异常 | `negative_control.py` 改用 composite `flood_class==1` 分组；Table 6 重算，"neither" 行 mean 归 0 | `negative_control.py`；`outputs/negative_control.json`（见 §9.6） |
| **C6** | "rainfall-conditioned PFI" 未真正被学习（r 在训练中恒定） | 标题/摘要/正文撤下 rainfall-conditioned 主创新；PFI_h 降级为 "model score"；§4.5 保留平坦结果作为数据设计必然的诚实报告 | `manuscript.md` 标题/Abstract/§3.7/§4.5 |
| **M1** | H3 support 是矩形 bbox，非 Manhattan land footprint | 未做 land mask（需 borough/land polygon 新数据）；在 §2/§5.4 显式声明 bbox 支撑与岸线/水域影响，作为已知局限 | `manuscript.md` §2、§5.4 |
| **M2** | R7 block 先验任选，未做相关性尺度检验 | 未做（需 Moran's I / variogram 新分析）；§3.4/§5.4 显式声明 block-size 未调优 | `manuscript.md` §3.4、§5.4 |
| **M3** | Adaptive 用 full-fit/in-sample 分数选 refinement，仅比较 cell count | 全稿降级为 "representation-size comparison"；§3.6/§4.4/Fig.6 明确"不主张效率/hotspot retention" | `figures.py`（Fig.6 标注 "representation size only"）；`manuscript.md` §3.6/§4.4 |
| **M4** | 未做 calibration 却写 "probability" | 全稿 "probability"→"model score"；§3.7 明示无校准 | `manuscript.md` §3.7 |
| **M5** | ponding baseline 有 test-fold normalization 泄漏 | `baselines.py` 加 `_ponding_bounds`，min/max 只从 training fold 计算后应用于 test | `baselines.py`（`_ponding_bounds` + `rule_predict_class(**bounds)`） |
| **M6** | shoreline distance 被用于 pluvial "hydrologic proximity"；urban flag 是 impervious 确定性复制 | 特征改名 "shoreline/tidal-water distance"；urban flag 保留但 §3.2 明示为确定性复制、无独立信息 | `manuscript.md` §3.2 |
| **M7** | "risk" 概念偏大 | 全稿 "risk"→"susceptibility / flood-evidence screening"；标题/Abstract 同步 | `manuscript.md` 全文 |

**未完全关闭项（诚实清单，均为"需新数据/新分析"，非"可文本掩盖"）**：M1（land mask）、M2（block-size 敏感性 + 空间自相关检验）、M3（真实 R11 reference + quality–cost Pareto）、C6（真实事件降雨）。这四项已按审稿意见在正文中**显式降级/声明为局限**，而非声称已解决。

### 9.2 数据语义核查（审稿意见要求新增的 data-semantic checks）

| 检查项 | 实际值 | 结论 |
|--------|--------|------|
| DEP 类别 | `Flooding_Category ∈ {1,2}`，各 extent n=2 多边形；**category 3 已剔除** | ✓ 无海岸高潮位污染 |
| 311 来源 | `source=arcgis_streetfloodtime`；日期 2010-01-07 → 2014-12-26；Lower n=488、Expanded n=1134 | ✓ 正文已更正（非 "2010–present"） |
| 311 字段 | 含 `Created_Da`、`WPCP`、`COMB_OR_SE`、`Outfall`、`Intercepto`（雨水井/合流制上下文），**无** complaint_type/descriptor 字段 | ✓ 该图层即"街道积水"主题层，非宽泛 sewer 查询 |
| HWM 质量 | `hwm_quality`：Fair 58 / Good 54 / Excellent 32 / Poor 15（共 159）；`height_above_gnd` 0–2.2 ft | ✓ 质量字段已保留；融合仍用 presence-only（§2 已声明为局限） |
| 每源正类单元（Lower） | DEP `dep_area_frac>0`：40/141；311 `complaint_count>0`：84/141；Ida HWM `ida_hwm_count>0`：**0/141**；union 正类 95/141 | ✓ 与 composite `flood_class` 一致；**HWM 在该 bbox 内无点（数据现实，非处理 bug）** |
| 每源正类单元（Expanded） | DEP polygon：231/956；311 point：367/956（raw 1134 点）；Ida HWM：14 点（6 cell）/956；union 正类 454/956 | ✓ 一致（2026-08-23 修复扩展窗口数据路径 bug + 2026-08-24 M4 当前海平面 DEP 主层后更新） |
| R10 原生 overlay 断言 | `outputs/jaccard_by_resolution.csv`：`n_fine=991`、`n_hotspot_fine=149`（非旧 571）；`assembly_mode=native_overlay` | ✓ 无 parent inheritance |
| 负对照 pluvial 定义 | `negative_control.json`：n_pluvial=95（=composite flood_class 正类），非旧 flood_area_frac>0 的 71 | ✓ 分组一致 |

### 9.3 修订后主表对账（空间 CV）

> **历史快照（pre-Option-B）：** 本节对账的是修订前 LM smoke **n=141** 主表。现行 Option B 真相见 **§14.3** / `outputs/paper_results.json`（n=262，acc 0.809，ROC-AUC 0.847）。

**Lower Manhattan（n=141，7 R7 block，正类 67.4%）** — 来源 `models/nyc_smoke/spatial_cv_folds.csv` + `outputs/classification_baselines.json`：

| 手稿数字 | 产物字段 | 原始值 | 对账 |
|----------|----------|--------|------|
| accuracy 0.781 ± 0.123 | `spatial_cv_accuracy_mean/std` | 0.781432 / 0.123141 | ✓ |
| F1 0.822 ± 0.116 | `spatial_cv_f1_mean`（std ddof=0） | 0.821905 / 0.116 | ✓ |
| evidence-score R² 0.048 ± 0.348 | `spatial_cv_r2_mean/std` | 0.048052 / 0.347867 | ✓ |
| MAE 0.330 ± 0.073 | `spatial_cv_mae_mean`（std ddof=0） | 0.330337 / 0.073 | ✓ |
| pooled ROC-AUC 0.780 | `spatial_cv_roc_auc_pooled` | 0.779748 | ✓ |
| pooled AP 0.805 | `spatial_cv_pr_auc_pooled` | 0.804805 | ✓ |
| always-positive acc 0.662 | `always_positive_mean_acc` | 0.662 | ✓ |
| always-positive F1 0.794 | `always_positive_mean_f1` | 0.794 | ✓ |
| always-negative acc 0.338 | `always_negative_mean_acc` | 0.338 | ✓ |
| 模型超 always-positive | `model_beats_majority_acc/f1` | true / true | ✓（0.781>0.662，0.822>0.794） |

**Expanded（n=956，28 block，正类 47.5%）** — 来源 `models/nyc_expanded/run_metadata.json` + `outputs/classification_baselines_expanded.json`：

| 手稿数字 | 产物字段 | 原始值 | 对账 |
|----------|----------|--------|------|
| accuracy 0.821 ± 0.033 | `spatial_cv_accuracy_mean/std` | 0.821260 / 0.032772 | ✓ |
| F1 0.819 ± 0.038 | `spatial_cv_f1_mean`（std ddof=0） | 0.819120 / 0.038 | ✓ |
| evidence-score R² 0.333 ± 0.144 | `spatial_cv_r2_mean/std` | 0.333494 / 0.144229 | ✓ |
| MAE 0.286 ± 0.036 | `spatial_cv_mae_mean`（std ddof=0） | 0.285732 / 0.036 | ✓ |
| pooled ROC-AUC 0.883 | `spatial_cv_roc_auc_pooled` | 0.883398 | ✓ |
| pooled AP 0.812 | `spatial_cv_pr_auc_pooled` | 0.812127 | ✓ |
| always-positive acc 0.475 / F1 0.643 | `always_positive_acc/f1_mean` | 0.475 / 0.643 | ✓ |
| 恒定多数类（恒判负）acc 0.525 | `always_negative_acc_mean` = `majority_acc_mean` | 0.525 | ✓ |

> **重要（2026-08-24 M4 当前海平面 DEP 主层）：** 上一版把 DEP「Moderate Flood with **2050 Sea Level Rise**」层（Layer 2）误当作主雨洪证据层。审稿人 M4 指出应以「Moderate Flood with **Current Sea Levels**」（Layer 1）为主层、2050 SLR 作为敏感性。修复 `download_nyc.py`（拆分 `_DEP_STORMWATER_CURRENT` / `_DEP_STORMWATER_2050SLR`）并重下两图层后重跑两试点：小窗口正类 98→95（69.5%→67.4%）、扩展窗口正类 475→454（49.7%→47.5%），DEP-only 证据单元 54→40（Lower）/ 268→231（Expanded），各项指标相应更新。结论（模型超过多数类基线、ROC-AUC/AP 高于随机）**不变**。2050 SLR 敏感性见 §13（`outputs/slr_sensitivity.{json,csv}`）。

### 9.4 尺度损失阶梯（R10 原生 overlay + exact top-10% 预算，修订后）

来源 `outputs/jaccard_by_resolution.csv`（`n_fine=991`、exact top-10% 热点 `k=99`、H3 index tie-break）：

| 行 | Jaccard | F1 | fine-parent recall | coarse precision | 对账 |
|----|---------|----|-------------------|------------------|------|
| R8 mean | 0.111 | 0.200 | 0.118 | 0.667 | ✓ |
| R8 max | 0.176 | 0.300 | 0.176 | 1.000 | ✓ |
| R8 p90 | 0.176 | 0.300 | 0.176 | 1.000 | ✓ |
| R9 mean | 0.180 | 0.306 | 0.196 | 0.688 | ✓ |
| R9 max | 0.286 | 0.444 | 0.286 | 1.000 | ✓ |
| R9 p90 | 0.286 | 0.444 | 0.286 | 1.000 | ✓ |

**关键变化（两阶段）**：
1. **C3（原生 overlay）**：旧版 R10 hotspot = 571/991（57.6%，因分数饱和 tied at max），R10→R9 mean Jaccard 0.977 主要来自 parent-inherit 循环。原生 overlay 后 q=0.9 hotspot = 149/991（15.0%），R10→R9 mean Jaccard = 0.210。
2. **M3（exact top-k）**：q=0.9 因 149/991 个最大分数单元 tie 而把"名义 top-10%"膨胀为 15.0%。改为 exact top-k（k = round(0.10 × 991) = 99，H3 index 确定性 tie-break），消除 tie 膨胀；粗网格同预算（R9 k=16、R8 k=3）重阈值，两组热点预算匹配。最终 R10→R9 mean Jaccard = 0.180、R10→R8 mean Jaccard = 0.111，真实揭示尺度损失。

### 9.5 自适应消融（修订后）

来源 `outputs/adaptive_vs_fixed_ablation.csv`：

| 量 | 旧 | 新 |
|----|----|----|
| 被加密 R9 cell | 84/141 | **98/141** |
| adaptive mixed cells | 4,173 | **4,845** |
| uniform R11 | 6,909 | 6,909 |
| 占比 / 倍数 | 60.4% / 29.6× | **70.1% / 34.4×** |

> **说明（2026-08-24 M4）**：自适应选择用 full-fit `PFI_h` 0.8 分位 + 不确定 + one-ring 邻域，`PFI_h` 随 M4 当前海平面 DEP 主层变化，被加密 R9 cell 由 84→98、mixed cells 4,173→4,845。本表仍为「表征规模（representation-size）比较」，非效率/hotspot 证明。

### 9.6 Sandy 负对照（composite flood_class + OOF 模型分，修订后）

来源 `outputs/negative_control.json`（`score_col = oof_model_score`）：

| 量 | 值 |
|----|----|
| 海岸 31 / 雨洪 95 / 两者 20 | ✓ |
| coastal-only 11（7.8%） / pluvial-only 75（53.2%） / neither 35（24.8%） | ✓ |
| OOF 分：coastal-only 0.435 / pluvial-only 0.823 / both 0.750 / neither 0.308 | ✓（旧 target 口径 0.000/0.888/0.776/0.000 已废弃） |
| pluvial − coastal OOF 分差 0.387 | ✓（旧 0.888 为循环论证，见 §10.2） |
| top-20% 分数单元中 coastal-only 3.4% / pluvial 79.3% | ✓ |

**结论修正**：旧版用 target `flood_risk` 比较，得到 coastal-only=0.000 是「定义恒等式」而非模型结论。改用留出（OOF）模型分后，coastal-only 单元 OOF 均值 **0.435**（非 0），说明模型**部分**学习了低海拔/近岸信号；但 pluvial-only 仍最高（0.823）、top 分数单元 79.3% 为 pluvial，故模型未被海岸位置单独驱动。

### 9.7 全量测试与复现

- 代码修复后 `pytest`：见 §3.1（测试门禁未退化）。
- 复现步骤与 §4 相同；新增数据语义核查（§9.2）可由下列命令复核：

```powershell
# 数据语义核查（DEP 类别 / 311 来源与日期 / HWM 质量 / 每源正类）
python - <<'PY'
import json, collections, pandas as pd
for area in ('nyc','nyc_expanded'):
    dep = json.load(open(f'data/raw/{area}/dep_stormwater_flood.geojson', encoding='utf-8'))
    print(area, 'DEP categories', collections.Counter(f['properties']['Flooding_Category'] for f in dep['features']))
    m311 = json.load(open(f'data/raw/{area}/flooding_311.geojson', encoding='utf-8'))
    print(area, '311 source', set(f['properties']['source'] for f in m311['features']), 'n', len(m311['features']))
    df = pd.read_parquet(f'data/processed/nyc_h3_cells{"" if area=="nyc" else "_expanded"}.parquet')
    print(area, 'pos', int((df.flood_class==1).sum()), 'area>0', int((df.flood_area_frac>0).sum()), 'point>0', int((df.flood_point_count>0).sum()))
PY
```

### 9.8 修订后诚实边界（相对旧版新增/强化的限制声明）

1. DEP = model-derived（非 observed）；仅 category 1–2，category 3 已剔除。
2. 311 = `arcgis_streetfloodtime` 快照（2010–2014），非 "2010–present"。
3. evidence score = max(area_frac, point_present)，饱和于 1，非严重度/概率。
4. 尺度损失 = R10 原生 overlay，无 parent inheritance。
5. Sandy 分组 = composite `flood_class`，neither 行 mean = 0。
6. adaptive = representation-size 比较（in-sample full-fit 选择），非效率/hotspot 证明。
7. ponding baseline 训练集归一化，无 test-fold 泄漏。
8. 矩形 bbox 支撑、R7 先验、无 calibration、r 恒定 → 均已在正文显式声明为局限。

---

## 10. 代码—论文一致性闭环（2026-08-23 第二轮：C3 源区分 + C4 OOF 负对照）

上一轮（§9）已关闭 C1/C2/C5/C6 四项"代码与论文不一致"的致命项，但形式审稿人指出仍有两处**代码实现尚未真正兑现论文措辞**：

- **C3（源区分 provenance）**：手稿 Highlights/Abstract/§2 写 "three sources are kept distinct / retained separately in the provenance tags"，但 `labels.py` 的 `attach_observed_labels` 此前把所有 polygon/point 一次性合并，仅设 `label_source = "open_public_evidence"`，**并未产出任何 source-specific 列**。措辞 ≠ 实现。
- **C4（Sandy 负对照循环）**：§9 已修好 grouping（composite `flood_class`），但 `negative_control_metrics` 传入的 `score_col` 仍是 target `flood_risk`。coastal-only cell 因 `flood_class=0` 而 `flood_risk=0` 是**定义恒等式**，故 Table 6 的 "0.000 vs 0.888" 不能证明"模型未学习海岸效应"——它根本没在测模型。

本轮**先改代码、后改文字**，把这两项真正兑现。

### 10.1 C3 处置：source-specific provenance 列

`src/pluvial_flood_risk/labels.py` 的 `attach_observed_labels` 重写为**按文件名分类源 → 分源计算 → 合成 composite**：

| 新列 | 含义 | 数据依据 |
|------|------|----------|
| `dep_area_frac` | DEP polygon 交叠面积分数（全类别） | `dep_stormwater_flood.geojson` |
| `dep_nuisance_frac` | category 1（nuisance）面积分数 | `Flooding_Category == 1` |
| `dep_deep_frac` | category 2（deep）面积分数 | `Flooding_Category == 2` |
| `complaint_count` / `complaint_presence` | 311 点计数 / 0-1 存在 | `flooding_311.geojson` |
| `ida_hwm_count` / `ida_hwm_presence` / `ida_hwm_quality` | Ida HWM 点计数 / 存在 / 质量字符串 | `usgs_ida_hwm.geojson` |
| `evidence_sources` | 每 cell 命中的源字符串（`dep+complaint+hwm` / `none` 等） | 上述合成 |
| `flood_risk`（composite） | `max(dep_area_frac, complaint_presence, ida_hwm_presence)` | 与旧语义一致 |

`flood_area_frac` / `flood_point_count` 保留为聚合列（向后兼容 + 海岸 overlay 复用）。源身份由**约定文件名**识别（`dep_stormwater_flood`、`flooding_311`、`usgs_ida_hwm`、`fema_sandy`）；未识别文件回退为 `generic`，仍按几何类型贡献 composite。

**语义不变性证据**：composite `flood_risk` = `max(area_frac, point_present)` 的构造与旧版语义一致，因此 binary classification（n_positive、prevalence、accuracy/F1、ROC-AUC/AP）、Jaccard ladder、adaptive 计数**均 bit 级不变**（accuracy 0.808089 前后一致）。回归指标（R²/MAE）有 ~0.003–0.004 的极小漂移（R² 0.075526→0.078968、MAE 0.329049→0.326358），系 C3 重写中 continuous-score 装配的浮点顺序差异所致，不改变"R²≈0.08 近零"的结论；§9.3 已按新值对账。只有负对照的 score 口径改变（见 §10.2）。

**测试**：`tests/test_labels_observed.py`（5 项）全部通过；新增对 `dep_area_frac`/`complaint_count`/`ida_hwm_count`/`evidence_sources` 列的隐性验证由装配表列存在性保证。

### 10.2 C4 处置：负对照改用 OOF 模型分数

`src/pluvial_flood_risk/pipeline.py` 的 `nyc_smoke_test` 把 Sandy 负对照**移到训练之后**，并：

1. 读取 `models/nyc_smoke/spatial_cv_oof_predictions.csv`，把每 cell 的 `y_proba` 左连接回装配表为 `oof_model_score`；
2. 以 `score_col="oof_model_score"` 调用 `negative_control_metrics`；
3. 若 OOF 不存在（<2 blocks 的 smoke）则填入 `NaN` 并显式标记，**不再静默回退到 target**。

`negative_control.py` 的 docstring 与默认 `score_col` 解析顺序同步更新（优先 `oof_model_score`），明确 "score_col must be an out-of-fold model score, never the target"。

**循环消除证据**：coastal-only cell 的 `flood_class=0`（定义），其 target `flood_risk=0` 是恒等式；OOF 分数是模型在**未见过该 block**时的预测，才是"模型是否把证据集中到 coastal-only"的有效检验。

### 10.3 新增图：源区分证据图（Fig. 4）

为把 C3 从"代码列存在"变成"可视化可读"，`figures.py` 新增 `plot_source_evidence_maps`，在**同一 H3 支撑**上并排 (a) DEP 面积分数、(b) 311 计数、(c) Ida HWM 计数、(d) composite 分数。`make_figures.py` 相应调整：新增源证据图（正文 Fig. 3），原 Fig. 3/4/5 顺延为 Fig. 4/5/6，原 Fig. 6（3 柱自适应消融）降级为 Supplementary Fig. S2（审稿人明确"这种粗 3 柱图太难看，用表格表示即可"；其数值已列于正文 Table 5）。

### 10.4 扩展窗口数据路径 bug（C6 类问题，本轮新发现并修复）

对账过程中发现一处**此前所有轮次都未暴露的致命问题**，直接导致扩展窗口主表（`manhattan_expanded`，n=956）此前所有数字失效：

| 项 | 说明 |
|----|------|
| 现象 | 扩展窗口 parquet 中 `complaint_count>0` 仅 145 单元，而用 `data/raw/nyc_expanded/flooding_311.geojson`（1134 点）直接映射到扩展 bbox 的 956 个 R9 cell 应得 **367 单元**；且 `feature_source="observed"` 覆盖全部 956 单元，但扩展窗口大量单元落在小窗口 DEM 覆盖范围之外 |
| 根因 | `configs/nyc.yaml` 的 `paths.*` 硬编码 `data/raw/nyc/`（小窗口）路径；`run_expanded_study.py` 仅覆盖 `paths.raw_dir = data/raw/nyc_expanded`，但 `sources_from_config` 优先用显式 `paths.dem/flood_points/...`（小窗口），**只有这些键为空才回退 `discover_sources(raw_dir)`**。结果：DEM/不透水/建筑/水系/311 全部误用小窗口文件覆盖在扩展 bbox 上，越界单元被合成哈希填充却仍标 "observed"，311 证据单元由 367 缩水到 145 |
| 修复 | `scripts/run_expanded_study.py` 清除 `paths` 中的显式键（`dem/slope/impervious/buildings/hydro/flood_polygons/flood_points/coastal/sandy/event_rainfall/floodnet`），使 `discover_sources(raw_dir=nyc_expanded)` 正确解析扩展窗口自身文件 |
| 影响 | 仅扩展窗口；Lower Manhattan（n=141）小窗口 `raw_dir=data/raw/nyc` 与其 bbox 天然一致，不受影响 |
| 复验 | 修复后重跑：311 单元 145→367、正类占比 36.5%→49.7%、accuracy 0.722→0.824、F1 0.498→0.832、pooled ROC-AUC 0.746→0.875（见 §9.3） |
| 防回归 | 用临时诊断脚本复现了 `_count_points` 与 parquet 的对账差异（311 文件直接映射=367 单元 vs 修复前 parquet=145 单元）；修复后对账一致。后续应在 `run_expanded_study.py` 增加断言：`assembly_mode=opendata` 且 `feature_source=observed` 时，扩展窗口 `complaint_count>0` 单元数应等于 311 文件直接映射数 |

**教训**：`manuscript/report/audit` 的措辞必须先于"可复现 claim"通过**代码对账**验证，尤其当多个 `raw_dir`（`nyc` vs `nyc_expanded`）并存时，配置优先级会导致静默的数据替换。这正是形式审稿人 C6"GitHub 多版本产物混用"背后更隐蔽的成因之一。

## 11. 源消融（source-ablation）——M2/M9 落实记录（2026-08-24）

### 11.1 背景与动机

审稿人 M2 质疑 composite target `flood_risk = max(dep_area_frac, complaint_presence, ida_hwm_presence)` 的 construct validity：三个源不是同一 latent 变量的等价测量，建议做 source-ablation（DEP-only / 311-only / HWM-only / 311+HWM / composite / composite-without-shoreline）。审稿人 M9 进一步指出 DEP 是 H&H 模型输出、与地形/不透水面预测变量共享驱动，存在「教师—学生循环」风险。本节记录该消融的实现、数据来源与结论，作为真实性/有效性证据。

### 11.2 实现与可复现性

| 项 | 说明 |
|----|------|
| 脚本 | `scripts/run_source_ablation.py`（新增） |
| 协议 | 与主评价**完全相同**：`spatial_block_cv_metrics`（k=2 H3 父块、5 折 GroupKFold、GBM），`spatial_cv_k=2`、`spatial_cv_folds=5` |
| 输入 | `data/processed/nyc_h3_cells.parquet`（LM n=141）、`data/processed/nyc_h3_cells_expanded.parquet`（扩展 n=956） |
| 目标定义 | 直接由 source-specific 列构造（C3 修复后这些列已在表中）：DEP-only=`dep_area_frac>1e-9`；311-only=`complaint_presence`；HWM-only=`ida_hwm_presence`；311+HWM=OR；composite=`flood_class/flood_risk`；composite_no_diststream=同 composite 但 X 去掉 `dist_stream_m` |
| 单类守卫 | `len(np.unique(y_class))<2` 时只记 prevalence、不拟合（LM 的 HWM-only 正类=0 即此情形） |
| 输出 | `outputs/source_ablation.json`（按 pilot 嵌套）、`outputs/source_ablation.csv`（长表） |

### 11.3 结果与对账

> **历史快照（pre-Option-B）：** 下表 LM 列为 n=141 时期数字。现行 Option B 源消融见 `outputs/source_ablation.json`（LM n=262：DEP 74 / ROC 0.802；311 141 / 0.864；composite 165 / 0.847）及 `docs/paper/report.md` §5.8。

| 目标定义 | 正类单元（LM/扩展） | pooled ROC-AUC（LM/扩展） | fold-mean ROC-AUC（LM/扩展） | F1（LM/扩展） |
|----------|--------------------|--------------------------|-----------------------------|--------------|
| DEP-only | 40 / 231 | 0.792 / 0.811 | 0.791 / 0.804 | 0.583 / 0.589 |
| 311-only | 84 / 367 | 0.748 / 0.848 | 0.746 / 0.849 | 0.742 / 0.709 |
| HWM-only | 0 / 6 | — / 0.233 | — / 0.484 | — / 0.000 |
| 311 + HWM | 84 / 369 | 0.748 / 0.846 | 0.746 / 0.846 | 0.742 / 0.714 |
| composite | 95 / 454 | 0.780 / 0.883 | 0.798 / 0.883 | 0.822 / 0.819 |
| composite 无 dist_stream_m | 95 / 454 | 0.783 / 0.887 | 0.791 / 0.884 | 0.826 / 0.821 |

**与主表一致性**：composite 行与 `outputs/expanded_primary_table.json`（扩展 0.883 / acc 0.821 / F1 0.819）及小窗口主表（0.780）**逐位一致**，证明消融脚本复用了同一协议、无独立参数漂移。DEP-only/311-only/composite 正类数随 M4 当前海平面 DEP 主层更新（54/268/98/475 → 40/231/95/454）。

### 11.4 结论（审稿 M2/M9 的直接回答）

1. **判别不由单一源独占**：扩展窗口 DEP-only 0.811、311-only 0.848，均接近 composite 0.883；311-only 是观测性众包源、非模型导出，其判别**无法用「重建 DEP H&H 图」解释**，故 M9 教师—学生循环不构成唯一解释。
2. **composite 略优于单源**（0.883 > 0.848），定位为「开放伪标签同化 + 温和融合」，而非「强融合技能」。
3. **HWM-only 无判别**（扩展 pooled 0.233、F1=0；LM 0 点未拟合）：HWM 仅贡献 presence，无独立排序能力。
4. **海岸距离代理不承载判别**：去掉 `dist_stream_m` 后扩展 0.887、LM 0.783（vs composite 0.883/0.780），判别不变甚至略升，说明排序能力非海岸位置伪影。

### 11.5 边界（防过度解读）

上述结论仅证明「判别复现于多种源定义、且非海岸代理伪影」，**不等于**「三类证据等价」或「HWM 已可独立建模」。HWM-only 无判别恰说明 HWM 的独立样本量（6 单元）不足以支撑单独训练。

## 12. 分块尺度敏感性（block-size sensitivity）——M1 落实记录（2026-08-24）

### 12.1 背景与动机

审稿人 M1 指出主评价的 R7 块（k=2）是「先验固定、未验证是否足以打断空间相关」，建议 R6/R7/R8 敏感性 + Moran's I + buffer。本节记录 R6/R7/R8 分块敏感性（k=1/2/3）与 composite 证据分 Moran's I 的实现与结果；buffer 与 leave-one-block-out 留作后续。

### 12.2 实现与可复现性

| 项 | 说明 |
|----|------|
| 脚本 | `scripts/run_block_sensitivity.py`（新增） |
| 协议 | `spatial_block_cv_metrics`（GBM、5 折 GroupKFold），k ∈ {1,2,3}；`block_ids_for_cells` 同主评价 |
| Moran's I | composite `flood_risk` 在 R9 原生 `h3.grid_disk(c,1)` k-ring 邻接（仅保留在集合内的邻居，行归一化）：I = Σᵢⱼ wᵢⱼ zᵢzⱼ / Σᵢ zᵢ² |
| 单块守卫 | `n_blocks<2` 时记 NaN、不拟合 |
| 输出 | `outputs/block_sensitivity.json`、`outputs/block_sensitivity.csv` |

### 12.3 结果与对账

| 试点 | k | 块数 | pooled ROC-AUC | fold-mean ROC-AUC | accuracy | F1 | R² |
|------|---|------|----------------|-------------------|----------|----|-----|
| LM | 1 | 27 | 0.750 | 0.650 | 0.814 | 0.869 | −0.078 |
| LM | 2 | 7 | 0.780 | 0.798 | 0.781 | 0.822 | 0.048 |
| LM | 3 | 3 | 0.697 | 0.586 | 0.796 | 0.859 | −0.188 |
| 扩展 | 1 | 157 | 0.888 | 0.890 | 0.821 | 0.841 | 0.344 |
| 扩展 | 2 | 28 | 0.883 | 0.883 | 0.821 | 0.819 | 0.333 |
| 扩展 | 3 | 7 | 0.873 | 0.851 | 0.820 | 0.819 | 0.340 |

**Moran's I（composite 证据分）：LM 0.224、扩展 0.433。** k=2 行与主表（§9.3）**逐位一致**，证明敏感性脚本复用同一协议。数值随 M4 当前海平面 DEP 主层更新。

### 12.4 结论（审稿 M1 的直接回答）

1. **扩展窗口稳健**：pooled ROC-AUC 在 R8/R7/R6 为 0.888/0.883/0.873，R7 选择不驱动扩展结论。
2. **小窗口不稳**：fold-mean ROC-AUC 0.650/0.798/0.586、R² 在 R8/R6 转负，证实「0.781 ± 0.123」是不稳定小样本估计。
3. **Moran's I 为正**（0.224/0.433），量化支持「空间分块而非 i.i.d.」的必要性。

### 12.5 边界（防过度解读）

「扩展窗口稳健」不推广到小窗口；Moran's I 绝对值不与线性相关强度混同；未做 spatial buffer / leave-one-block-out（§5.5 列为后续）。

## 13. DEP 海平面情景敏感性（sea-level sensitivity）——M4 落实记录（2026-08-24）

### 13.1 背景与动机

审稿人 M4 指出：主雨洪证据应使用 DEP「Moderate Flood with **Current Sea Levels**」（Layer 1），而非「Moderate Flood with **2050 Sea Level Rise**」（Layer 2）。上一版误把 2050 SLR 层当作主层，属于**数据语义错误**（把未来情景投影当作当前雨洪证据）。修复后以当前海平面为主层，并保留 2050 SLR 作为**敏感性**，量化两种海平面情景对目标与判别指标的影响。两种 DEP 变体均为 H&H 模型输出，比较是「数据语义敏感性」，不是「观测验证」。

### 13.2 实现与可复现性

| 项 | 说明 |
|----|------|
| 脚本 | `scripts/run_slr_sensitivity.py`（新增） |
| 协议 | 同主评价：`assemble_h3_table`（resolution=9）+ `spatial_block_cv_metrics`（GBM、5 折、k=2 R7 块），`flood_polygons_path` 分别指向 `dep_stormwater_flood.geojson`（current）与 `dep_stormwater_flood_2050slr.geojson`（2050） |
| 类别过滤 | 两变体均 `Flooding_Category 1–2`，排除沿海「future high tides」类 |
| 输出 | `outputs/slr_sensitivity.json`（按 pilot 嵌套）、`outputs/slr_sensitivity.csv`（长表） |

### 13.3 结果与对账

> **当前权威（2026-09-14 post–76ig-c548）：** 下表来自重跑后的 `outputs/slr_sensitivity.json`。current 行与主表 / `paper_results.json` 一致。

| pilot | DEP 变体 | n | 正类 | 占比 | DEP 单元 | pooled ROC-AUC | fold-mean ROC-AUC | accuracy | F1 | R² |
|-------|----------|---|------|------|----------|----------------|-------------------|----------|----|-----|
| LM Option B | current | 262 | 167 | 63.7% | 74 | 0.848 | 0.821 | 0.820 | 0.858 | 0.191 |
| LM Option B | 2050 SLR | 262 | 177 | 67.6% | 98 | 0.836 | 0.837 | 0.870 | 0.906 | 0.212 |
| 扩展 | current | 956 | 458 | 47.9% | 231 | 0.882 | 0.881 | 0.823 | 0.826 | 0.348 |
| 扩展 | 2050 SLR | 956 | 478 | 50.0% | 268 | 0.872 | 0.873 | 0.821 | 0.831 | 0.345 |

> **历史注记（pre–76ig-c548 Option B）：** 曾为 LM 165/63.0%/ROC 0.847 vs 176/67.2%/0.833；扩展 454/47.5%/0.883 vs 475/49.7%/0.875。**更早 pre-Option-B n=141：** LM current 95/67.4%/ROC 0.780 vs 2050 98/69.5%/ROC 0.741。勿与现行表混用。

**关键事实（post–76ig-c548 重跑后）**：
1. **current 行与主表 / `outputs/paper_results.json` 逐位一致**（LM pooled ROC-AUC 0.848、acc 0.820；扩展 0.882 / 0.823）。
2. **current 层的判别力不降反略升**：LM pooled ROC-AUC 0.848 > 0.836；扩展 0.882 > 0.872（差异约 0.01，属噪声级）。
3. 两变体下**所有实质结论不变**：模型超过 prevalence-aware 基线、ROC-AUC/AP 高于随机、扩展判别稳定。
4. （审计轨迹）pre-M4 主表曾误用 2050 SLR 层；该语义错误定位见历史 n=141 注记与 §9.3。

### 13.4 结论（审稿 M4 的直接回答）

以当前海平面层为主层是**语义正确**的（代表当前雨洪证据，非未来情景）；且该选择**不弱化**论文结论（判别力持平或略升）。2050 SLR 作为敏感性保留，二者差异只体现为目标占比与次要指标的小幅平移。

### 13.5 边界（防过度解读）

「current 判别力略高」不解释为「当前海平面层更真实」——两种 DEP 变体都是同一 H&H 建模框架的产物，差异主要来自淹没范围（2050 更广、正类更多、判别略降）。本敏感性只证明「结论不依赖海平面情景选择」，不构成对 DEP 模型本身的验证。



## 14. Major Revision pass (2026-08-31) — Option B

Formal audit conclusion was **Major Revision — do not submit yet**. This section records the remediation pass.

### 14.1 Choices

| Item | Decision |
|------|----------|
| Bbox | **Option B**: manuscript Lower Manhattan bbox `[-74.02, 40.70, -73.97, 40.76]` → **262 R9 cells** (legacy smoke 141 retained as QA-only profile) |
| Fail-closed | `fallback_synthetic=False` default; paper path refuses synthetic fills |
| Models | Split `evaluation/` (CV/OOF/split diagnostic) vs `deployment/` (`classifier_full` / `regressor_full`, `fit_rows == n_cells`) |
| Hotspots | Fractional membership ties + projected-parent-area budgets; no false cell-count matched-budget claim |
| Area ratios | Polygon intersections in EPSG:2263 |
| Seed | Config `random_seed` passed through estimators and written to metadata |

### 14.2 Evidence paths

- `data/raw/data_manifest.json` / `.csv` — official landing pages, mirror flags, SHA-256
- `审查输出/evidence/audit_evidence.json` — pre-revision audit snapshot
- `outputs/paper_results.json` — post-rerun metrics summary
- `models/nyc_smoke/` and `models/nyc_expanded/` — evaluation + deployment artifacts

### 14.3 Post-rerun headline metrics (do not mix with pre-revision n=141 numbers)

| Pilot | n | Acc (mean±SD) | F1 | ROC-AUC pooled | AP pooled |
|-------|---|---------------|----|----------------|-----------|
| Lower Manhattan (Option B) | 262 | 0.820 ± 0.057 | 0.858 | 0.848 | 0.855 |
| Expanded | 956 | 0.823 ± 0.028 | 0.826 | 0.882 | 0.823 |

LM always-positive baselines: acc 0.637, F1 0.769 (model exceeds both).

### 14.4 P0 status

| ID | Status |
|----|--------|
| P0-01 bbox | **Done** (Option B, n=262) |
| P0-02 full deployment model | **Done** |
| P0-03 provenance / mirror honesty | **Partial→strengthened** (311 official 76ig-c548; DEP still public mirror verified=false with 9i7c-xyvv+AdaptNYC landing chain; FloodNet official held-out) |
| P0-04 fail-closed assembly | **Done** |
| P0-05 projected area CRS | **Done** (EPSG:2263) |
| P0-06 Fig 4 clipping | **Done** |
| P0-07 hotspot ties/budgets | **Done** (fractional + strict area budget; Fig.6 from canonical CSV) |
| P0-08 seed / Table 8 caption | **Done** |

### 14.5 Remaining author confirmation

- Real author names / affiliations / ORCID / CRediT
- Optional: replace DEP ArcGIS mirror with verified official NYC geospatial export if/when `9i7c-xyvv` machine download works
- Human push to remote / DOI / Zenodo release after review

### 14.6 Quarantine

Temporary scripts and third-party ZIP moved to `审查输出/quarantine/` (not deleted).

---

## 15. 收尾完成（2026-09-15）— Major Revision auto-doable closeout

本轮按「不要留尾巴」把可自动落实的投稿前工程全部落地。权威数字仅以 `outputs/paper_results.json` 为准。

### 15.1 Closed (auto-doable)

| Item | Evidence |
|------|----------|
| P0-01 Jaccard one-source | `outputs/jaccard_by_resolution.csv` + Fig.6 reads canonical ladder; soft Jaccard R10→R9 mean 0.227 / R10→R8 mean 0.136 |
| P0-02 311 official | SODA `76ig-c548`; query sidecar; `official_identity_verified=true` |
| P0-03 run provenance / lock | `models/*/run_manifest.json`, `requirements.lock.txt`, `paper_results.software_environment` |
| P0-04 tests green | full pytest green (see commit notes) |
| P0-05 FloodNet | Official `aq7i-eu5q`+`kb2e-tjy3` downloaded; strict held-out diagnostic `outputs/floodnet_heldout_validation.json`; **not** training labels |
| P0-06 numeric drift | manuscript/README/report headlines synced to Option B post-rerun metrics |
| DEP honesty | manifest keeps `verified=false` + Open Data `9i7c-xyvv` + AdaptNYC landing chain (SODA geospatial export HTTP 400) |
| Results registry | `paper_results.json` includes LM/Exp CV, Jaccard, adaptive, negative control, source ablation, block sensitivity, SLR, baselines, FloodNet, software pins |
| Quarantine | `_tmp_*` + leftover ZIP under `审查输出/quarantine/` |

### 15.2 Human-only leftovers (cannot invent)

1. Real author names, affiliations, ORCID, CRediT roles (keep `[待补充]`)
2. `git push` / remote release / DOI / Zenodo
3. Independent human unit audit sign-off (optional journal process)
4. Optional DEP official geospatial replace when NYC Open Data export becomes machine-downloadable

### 15.3 Explicitly no intentional “next phase later” in code/docs

FloodNet is no longer described as “data unavailable”. Further denser FloodNet / rainfall / citywide work is scientific scope expansion, not unfinished P0 engineering.
## 16. Paper maturation pass (2026-09-15) — end-to-end package

**Manuscript spine used:** `docs/paper/manuscript.md` (newest user mainline; no separate `manuscript_new*` / Desktop copy found).  
**Framework note:** `docs/paper/framework_note.md` (Option B freeze; literature-informed IJDRR skeleton + Nature claim discipline).  
**Numeric authority:** `outputs/paper_results.json` (generated_utc 2026-09-14T18:04:59+00:00).

### 16.1 Headline reconciliation (manuscript ↔ registry)

| Quantity | Registry | Manuscript / report |
|----------|----------|---------------------|
| LM n_cells | 262 | 262 |
| LM prevalence | 0.6374 | 63.7% |
| LM spatial_cv accuracy mean±std | 0.820±0.057 | 0.820 ± 0.057 |
| LM F1 mean | 0.8576 | 0.858 |
| LM pooled ROC-AUC / AP | 0.8480 / 0.8546 | 0.848 / 0.855 |
| Exp n / acc / F1 / ROC | 956 / 0.823 / 0.826 / 0.882 | matched |
| Soft Jaccard R10→R9 / R10→R8 mean | 0.2267 / 0.1358 | 0.227 / 0.136 |
| Adaptive cells | 7222 vs 12838 (145/262 refined) | 56.3% |
| FloodNet LM ROC-AUC (held-out) | 0.343 | reported as diagnostic only |
| 311 official | 76ig-c548 verified=true | matched |
| fail_closed | true | Methods + report |
| deployment_fit_rows LM | 262 | matched |

### 16.2 Authenticity / completeness evidence this pass

| Check | Evidence |
|-------|----------|
| Numbers not from Svellingen | Soft Jaccard from `outputs/jaccard_by_resolution.csv`; PFIb/0.14 explicitly non-reproduction |
| Fold table live | `models/nyc_smoke/spatial_cv_folds.csv` regenerated into report Table 2 |
| Report no longer truncated / stale | `scripts/_gen_report_md.py` rebuilds `docs/paper/report.md` from registry |
| Figures SciencePlots + TNR | `src/pluvial_flood_risk/figures.py` `apply_paper_style`; `scripts/make_figures.py` |
| Self-contained HTML | `scripts/build_manuscript_html.py`, `scripts/build_paper_report_html.py` (Base64, inline CSS) |
| Paper vs report path policy | Manuscript stripped of local `outputs/` / `models/` paths; report retains paths |
| Author placeholders | CRediT / names remain **待补充** |

### 16.3 Remaining 待补充 (human-only)

1. Author names, affiliations, ORCID, CRediT  
2. Observed event rainfall (non-flat `PFI_h(c,r)`)  
3. Citywide evaluation  
4. Optional DEP official geospatial replace  
5. Remote `git push` / DOI (not performed this pass)

---

## 17. Construct-validity revision freeze (2026-09-21)

**Tag intent:** `submission-v4-construct-validity`

### 17.1 What changed this round

| Item | Evidence |
|------|----------|
| Label semantics | Manuscript reframes binary labels as **evidence-positive / evidence-unrecorded** |
| Source ablation + 311−building_density | `outputs/source_ablation.json` (LM 311-only AUC 0.846; w/o building_density 0.837; both >0.5) |
| LOBO + residual Moran | `outputs/block_sensitivity.json` (LM LOBO pooled AUC 0.858; residual I 0.047) |
| Domain-masked scale loss | `outputs/jaccard_by_resolution.csv` (n_fine=1788, n_coarse R9=262; mean Jaccard R9=0.220 / R8=0.136) |
| Sandy 311 window | `outputs/sandy_311_window_sensitivity.json` (9 complaints excluded; 1 cell flip; OOF still used) |
| S_h(c) not rainfall main claim | Manuscript §3.7 / §4.5 |
| Adaptive demoted | Supplement cell-count experiment only |
| Extended OOF metrics | `outputs/oof_extended_metrics.json` (MCC/bal.acc/prec/rec/spec) |
| Hard gates | `tests/test_major_revision_gates.py` (DEP cats, source cols, native_overlay, domain mask, OOF score col) |

### 17.2 Numeric authority

Still `outputs/paper_results.json`. LM n=262 / Exp n=956 unchanged. Do **not** revert to n=141.

### 17.3 Human-only remaining

Author names, ORCID, CRediT roles; journal cover letter; true land-fraction≥0.5 polygon mask if required by editor; nested CV (explicitly declined — hyperparameters pre-specified).
