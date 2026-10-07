# 验收报告：R12–R21 ChatGPT 协作迭代（论文成熟化）

**日期：** 2026-08-18
**仓库：** https://github.com/Coucou2016/pluvial-flood-risk-DGGS-H3
**顾问会话：** https://chatgpt.com/c/6a8086e4-3a30-83ea-960b-cde100e0f3b2
**模式：** Cursor = 唯一本地执行者；ChatGPT = 文本顾问（浏览器 live 对话，每轮回复已归档 `artifacts/chatgpt_reply_R*.md`）。

## 1. 协作总览

| 轮次 | 主题 | 回复归档 |
|------|------|----------|
| R12 | 创新性定位 + 相关工作 | `chatgpt_reply_R12.md`（见 round_log） |
| R13 | Methods 可复现性（4.1–4.8 逐字） | `chatgpt_reply_R13.md`（见 round_log） |
| R14 | Results 表/图注/图格式 | `chatgpt_reply_R14.md`（见 round_log） |
| R15 | 学术语气 + 去 AI 痕迹 | `chatgpt_reply_R15.md`（见 round_log） |
| R16 | 图格式深度润色（本地执行 R14 遗留） | —（无新 round） |
| R17 | 投稿就绪 + 不可变发布 | `chatgpt_reply_R17.md` |
| R18 | 综合章节（Abstract/Intro/Discussion/Conclusion） | `chatgpt_reply_R18.md` |
| R19 | 跨章节一致性 | `chatgpt_reply_R19.md` |
| R20 | 框架 + Results 散文 + 图注 | `chatgpt_reply_R20.md` |
| R21 | 最终验收（sign-off） | `chatgpt_reply_R21.md` |

**共 10 轮 live 协作**（R12–R21；R16 为本地执行）。ChatGPT R21 明确结论：论文已具备连贯、可辩护的方法论贡献，**建议停止实质性散文修改**（再改仅剩风格性churn）。

## 2. 代码库基线

- 核心模块：`src/pluvial_flood_risk/`（`figures.py`、`metrics.py`、`spatial_cv.py`、`pipeline.py`、`model.py`、`baselines.py`、`adaptive.py`、`negative_control.py`、`rollups.py`）。
- 实验脚本：`scripts/run_expanded_study.py`（扩展窗口 n=956 主表）、`scripts/compute_classification_baselines.py`（平凡基线物化）。
- 学术基线：Svellingen et al. 2026 IJDRR（PFIb → H3 聚合，Jaccard≈0.14）。

## 3. 提供给 ChatGPT 的上下文

每轮提供逐字文本包（`artifacts/chatgpt_paste_R*.md`）：创新性定位、Methods 全文、图注+表、AI 痕迹语料、综合章节、跨章节数字、Results 散文、最终摘要。数字均来自 `outputs/` 与 `models/` 的 live 产物，无一处臆造。

## 4. 采纳建议（要点）

- **创新性**：H3 作为「共同空间支撑」（learning + evaluation），而非「聚合网格」——架构级对比 Svellingen（R12/R20）。
- **相关工作**：补 Agonafir 2022a/b（NYC 311 报告偏差）、自适应分辨率前例（R12）。
- **Methods**：4.1–4.8 重写为代码可核验定义（种子 42、ponding 公式、R7 parent、quantile 0.9/0.8、PFI_h 无校准声明）（R13）。
- **基线修复**：`_majority_baseline` → `_constant_baselines`（区分恒判正/恒判负、折内一致聚合）（R11 遗留，R12 前已落地）。
- **判别指标**：OOF ROC-AUC + Average Precision (AP) 物化（R12 起贯穿全文）。
- **术语统一**：PR-AUC→AP、hook/stub→rainfall input、binding→formal、ida_like→Ida-like（R13/R14/R15/R19）。
- **图片**：PNG+PDF 矢量、mean±SD 参考带、数值标签、去 in-image 标题/footer（R14/R16/R20）。
- **综合章节**：argumentative economy，去掉「非 PFIb / 非 citywide」重复防御（R18/R19/R20/R21）。
- **投稿元数据**：CRediT / Funding / 利益冲突 / AI 声明、Highlights、alphabetical author-date、摘要压缩 ~330→~230 词（R17）。

## 5. 拒绝 / 推迟建议

- 机械性删除 em-dash / "Furthermore" / "the present study"：**拒绝**（非 AI 痕迹，节奏问题非词问题）（R15）。
- `PFI_h` 改名：**部分推迟**（跨代码/图/config，已加强 §1 消歧）（R12）。
- 参考文献改 IJDRR 编号 `[n]`：**推迟**（YPYW 允许一致格式；Elsevier 生产阶段处理；不手工重编号）（R17/R18）。
- CRediT 作者名单：**推迟给用户**（不臆造作者，保留 待补充 占位）（R17–R21）。

## 6. 本地修改与备份

- 修改：`manuscript.md`（10 轮累计）、`report.md`、`audit.md`、`highlights.md`、`README.md`、`figures.py`、`build_paper_report_html.py`。
- 时间戳备份：`docs/paper/backups/` → `20260818_0325_preR15`、`20260818_0420_preR17`、`20260818_0418_preR19`、`20260818_0424_preR21`。

## 7. 测试与数字锁定

- 全量测试：**58 passed, 1 skipped**（`.venv`，2026-08-18）。
- 数字锁定（与 live 产物一致，未改）：
  - 小窗口 n=141：acc 0.784±0.069 / F1 0.866 / 恒判正 0.808·0.893 / ROC-AUC 0.683 / AP 0.861 / 患病率 0.801。
  - 扩展 n=956：acc 0.642±0.148 / F1 0.608 / 多数类(负) 0.521 / ROC-AUC 0.703 / AP 0.723 / 患病率 0.479 / R² 0.525±0.112。
  - Jaccard R10→R8(mean) 0.167；adaptive/uniform 0.569；Sandy 负对照 coastal-only ≈5.7%。

## 8. 未验证风险（如实标注，不填数字）

- 观测事件降雨（当前为常数合成输入）：待补充。
- FloodNet 留出传感器验证：无可用传感器层。
- citywide 范围：仅两个 Manhattan pilot。
- CRediT 作者名单：待补充（投稿前必填）。

## 9. Git / 发布状态

- `master` 已推送（最新 `a733068`）。
- 注释标签 `paper-v1` 已推送，指向最终 R21 commit `b49379c5361f82587439afcfba13be33bb0b5910`。
- 全部数字自 R17 起未变；R18–R21 仅文字/逻辑/图注/表述润色，不影响复现性。
- 结论：**论文达到投稿就绪的方法论贡献水平，唯一硬性待办为 CRediT 作者名单（及可选：观测降雨、FloodNet、citywide 作为后续工作）。**
