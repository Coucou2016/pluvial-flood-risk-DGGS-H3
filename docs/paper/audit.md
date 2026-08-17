# 审查文档（Audit）：数据真实性、准确性与完整性证据

**用途：** 本文档用于证明手稿 `manuscript.md` 与研究报告 `report.md` 中的所有数字，均为**本仓库自身代码在本机数据上运行所得**，而非从参考文献（尤其 Svellingen et al. 2026 IJDRR 及其 PFIb / Jaccard 0.14 数字）或任何第三方论文中抄录；并证明结果**可逐条复算、可对账、无“做一半臆断一半”**。

**审查对象：** `docs/paper/manuscript.md`、`docs/paper/report.md`、`README.md` 中的全部量化结论。

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
| Jaccard 说明 | 手稿 §6.2 与图注明确：0.167 是本仓库开放标签在 R10→R8 mean 聚合下的结果，**不得**等同 Svellingen 0.14 |
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
