# W11 评审请求（2026-08-20）：写作风格 humanize（去除"研究总结/答辩/AI 整理稿"气质）

## 背景
W1–W10 已完成：写作框架重构（W1–W5）、图体系对齐（W6–W10，W10 已 sign-off）、数据真实性审计（audit.md）。本轮聚焦用户**持续不满意的唯一维度：写作风格/措辞**。

用户原话：目前论文写作带有较明显的"研究工作总结 / 审稿答辩 / AI 辅助整理稿"气质。要求按"不改变科学内容、结果和核心结论，只重做论文写法、逻辑组织和投稿体例"处理，参照参考论文（Svellingen et al. 2026 IJDRR）的写法/篇幅/逻辑组织，并结合 humanizer 原则（如 Manchester Academic Phrasebank）去除 AI 写作痕迹。

## 本轮注入文件（共 4 个）
1. `chatgpt_context_W11.md`（本文件）
2. `manuscript.md`（W10 更新后最新稿，含 Fig.4 caption 修正）
3. `reference_paper.md`（参考论文 Svellingen et al. 2026 IJDRR 全文 md，写作风格/篇幅/逻辑组织参照）
4. `audit.md`（数据真实性约束，确保你任何改写都不改变已锁定的数字）

## 任务（中文，结构化，每条给精确可落地 diff）

### A. 逐段诊断"研究总结/答辩/AI 痕迹"的具体位置
1. 通读 `manuscript.md`，逐段标出带有以下气质的具体句子/短语（给出原文 + 问题类型 + 改写建议）：
   - "工作总结"气质：像在汇报"我做了什么"，而非在论证"为什么这是有效的科学贡献"；
   - "答辩"气质：过多 defensive 括号说明、过多"我们/本研究"的自我指涉、过多"not / do not / does not"的防御性否定；
   - "AI 整理稿"气质：碎片化短句罗列、每句独立无连接、罗列式 listing（First, Second, Third / (i)(ii)(iii) 生硬）、模板化过渡词。
2. 特别指出：摘要（Abstract）当前一段密集罗列数字的写法，是否应参照参考论文拆成"目标/方法/结果/含义"的逻辑层次（**数字一个不改**，只调结构与衔接）。

### B. 引言（Introduction）逻辑组织重构建议
3. 对照 `reference_paper.md` 的引言递进结构（城市洪涝背景 → 社会成本 → 规划需求 → 易感性指数 → DRR 需求 → H3/DGGS → ML → 研究空白 → 研究问题），评估我方 `manuscript.md` 引言是否具备同样的"段落递进 + 段间连接词"逻辑。指出缺哪一环、哪些段可以合并/顺承。
4. 我方研究问题当前用 `(i)/(ii)/(iii)` 罗列，参考论文用自然语言三条 subsidiary questions。请给出改写建议（**三个问题的科学内容不变**，只改表述形式与衔接）。

### C. Methods / Results / Discussion 的段落衔接与措辞
5. 检查 §2 Study area and data、§3 Methods、§4 Results、§5 Discussion 的开头段，是否像"汇报清单"而非论文论证。给出每节开头 1–2 句的"论文式"改写（保持全部数字与结论）。
6. 检查残留的 defensive 括号（如 "not a reproduction of that value"、"these are observed flood labels, not verified inundation ground truth" 之类）。区分两类：**必须保留的科学诚实**（负对照非因果、非 citywide、非降雨条件判别等）与**可自然化**的技术描述，分别列出。

### D. 措辞层面的 AI 痕迹
7. 列出所有"工具栈罗列"式表述（如 "combining public flood observations with spatially blocked evaluation"），给出"集成贡献"式改写（参照参考论文 "The contribution of the paper is to demonstrate..." 的句式）。
8. 检查是否有滥用连接词（Moreover/Furthermore/Additionally 堆叠）、过度名词化、以及"本文/本研究"主语重复，给出修正清单。

## 约束（硬性）
- **不改变任何科学内容、结果、核心结论、全部数字**（R10=991/R9=160/R8=31、Jaccard ladder、CV 指标、adaptive 141/3933/6909、ROC-AUC/AP、R² 等一律原样）。
- 不改变图表编号、表结构、引用编号。
- 只做写法、逻辑组织、措辞、投稿体例（含 Highlights/Abstract 措辞，不含数字）。
- 每条建议必须给出**精确的原文 → 改写后** diff，不得泛泛而谈。

## 输出格式
按 A/B/C/D 四部分，每部分用表格或编号列表，每条含：位置（节/句）→ 问题 → 改写建议（精确文本）。最后给 MUST-FIX（真正影响"论文感"的）/ 建议 / 可选 分级，并说明是否 sign-off 当前写作风格。
