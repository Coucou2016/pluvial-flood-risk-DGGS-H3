本轮基于最新注入的 manuscript.md、audit.md、figures.py、参考论文全文以及两张重新渲染 PNG 做了复核。GitHub live master 本轮仍不能由我独立作为可靠证据源，因此仓库 tag/manifest 的判断以下均以注入的 audit 为准。IJDRR 当前 ScienceDirect 页面可访问，但其 journal-specific Guide for Authors 细则不能完整抓取；版面与 Highlights/AI 声明部分因此以 Elsevier 当前官方通用规范为基准。IJDRR 本身仍列出 Guide for Authors 入口。

总体判断：W7 的全部修复落地；科学内容没有新回归。W8 剩余主要是投稿级 prose polish、最终物理尺寸重渲染，以及一个重要的 release-tag 一致性问题。

A. Defensive prose 最后一次 sweep

不是所有 not 都应该删除。你现在最应避免的是"告诉审稿人不要怎样理解"的语气；真正涉及证据边界、训练泄漏、PFIb 符号碰撞的否定必须保留。

优先级 | 位置 | 当前表述 | 建议最小替换 | 处理
高 | Abstract | "evaluated without overstating performance" | "evaluated with explicit control for spatial dependence" | 改写
高 | §3.3 | "so that accuracy and F1 are never reported without a class-prevalence comparison" | "Accuracy and F1 are reported alongside these constant classifiers to provide a class-prevalence reference." | 改写
高 | §3.4 | "Random independent splits are computed for comparison but are not primary." | "H3-block spatial cross-validation is the primary evaluation; random independent splits are retained as diagnostic comparisons." | 改写
高 | §4.1 | "the full-fit index ... tracks the cross-validated surface closely (Pearson r = 0.51)" | "the full-fit index shows moderate spatial concordance with the cross-validated surface (Pearson r = 0.51)" | 改写
高 | §4.1 | "The maps are presented for visual inspection ... only; they carry no quantitative claim..." | "The maps provide a qualitative comparison of the assembled surfaces; quantitative predictive performance is reported in Section 4.2." | 改写
高 | §4.4 | "These statements concern cell counts only; wall-clock runtime, memory, and city-scale cost are not reported." | "This ablation measures representation size by cell count; runtime, memory use, and city-scale computational cost are outside the reported metrics." | 改写
高 | §5.1 | "the full-fit index closely reproduces the cross-validated surface; ... not an additional validation" | "the full-fit index shows moderate spatial concordance with the cross-validated surface. Validation is based on the out-of-fold metrics." | 改写
高 | §5.3 | "This is what distinguishes the framework..." | "Using the same hierarchy for these four operations extends H3 from a post-prediction visualisation layer to the learning and evaluation architecture." | 改写
高 | §5.3 | "deliberately conservative, but one caveat applies... not demonstrated... noted rather than resolved" | "The R7 block size is fixed a priori; its relation to the target's spatial autocorrelation range was not evaluated, so block-size sensitivity remains a limitation." | 改写
高 | §5.4 end | "Random-split accuracy must not displace spatial cross-validation in claims." | "Primary performance claims are based on spatial cross-validation; random-split accuracy is retained as a diagnostic comparison." | 改写
中 | §4.7 | "robustness check ... not as citywide skill" | "The expanded pilot provides a robustness check within Manhattan; citywide generalisation remains unevaluated." | 改写
中 | §5.1 | "higher [AP] ... does not imply stronger classification" | "Because AP is prevalence-dependent, the higher value in the smaller pilot is interpreted relative to its higher prevalence baseline." | 改写
中 | §5.4 item 1 | "neither of which is citywide New York City" | "Both are sub-city Manhattan extents." | 可改
中 | §5.4 item 4 | "ingestion of gauge or radar event rainfall is not implemented" | "The present analysis uses constant synthetic rainfall rather than event-specific gauge or radar rainfall." | 改写
中 | §5.4 item 8 | "not as citywide predictive skill" | "The R2 values are interpreted within their respective pilot extents." | 改写
中 | Conclusions | "they do not establish citywide operational skill" | "The evidence is limited to the two Manhattan pilot extents." | 改写
低 | §4.5 | "A non-zero response requires..." | "Evaluating rainfall responsiveness requires observed event rainfall with variation across intensities and model retraining." | 更自然

尤其建议改掉 closely。r=0.51 写成 "moderate spatial concordance" 比 "closely tracks/reproduces" 更稳健。当前 §4.1 的数值和 descriptive/validation 边界本身没有问题。

以下否定则建议保留，因为属于科学定义而非 defensive prose：
§3.5 "not a reproduction"——0.167 与 Svellingen 0.14 的定义确实不同。
§3.7 "not SHAP / permutation importance / PFIb"——PFI 符号碰撞使这句必要。
§3.8 Sandy 从 feature/target/model selection 排除且 never a training label——数据泄漏边界必须明确。
Fig. 1 Sandy never a training label——图自身需要自包含。
Fig. 2 full-fit 与 OOF 的区别——不能删掉，只可改成更正向的 "full-fit rather than out-of-fold"。
constant synthetic rainfall 导致当前 rainfall discrimination 未建立——这是核心证据范围。
§5.2 也不建议过度 humanize。Svellingen 比较必须保持"conceptual rather than numerical"的纪律；参考论文自身明确使用已有 PFI_b 做 H3 聚合，你这里的区别确实是方法结构而非数值比赛。

B. 最终 PDF / 图表版面

先给一个重要边界：本轮没有注入最终 manuscript.pdf，所以我不能核查实际分页、caption 是否孤行、表格是否在 PDF 中越界。我能核查的是出图源码的物理尺寸、实际 PNG 和 manuscript 表结构。

Elsevier 当前通用建议是最终图中文字通常约 7 pt，上下标不小于约 6 pt；典型目标宽度约为 90 mm 单栏、140 mm 1.5 栏、190 mm 双栏。

六张图：
图 | 当前源码尺寸 | 建议最终宽度 | 判定/最小动作
Fig. 1 workflow | 11.2 x 6.4 in | 190 mm | 需重渲染最终宽度。内部 box text 仅 8 pt；直接把 11.2 in 缩到双栏会低于理想最终字号。保持双栏，按 190 mm canvas 重设字体。
Fig. 2 spatial maps | 12.0 x 4.4 in | 190 mm | 需重渲染。当前 PNG 本身清楚，但源码 colorbar tick 8 pt、label 9 pt；直接整体缩放会过小。三面板应坚持双栏，不适合单栏。
Fig. 3 spatial CV | 6.4 x 3.4 in | 140 mm | 基本达标。适合 1.5 栏；不建议压到 90 mm。
Fig. 4 Jaccard ladder | 9.2 x 3.6 in | 190 mm | 达标结构。双 panel + shared legend 最适合双栏。
Fig. 5 resolution effects | 9.6 x 3.8 in | 190 mm | 达标结构。当前 (b) 已白字，raw points、matrix annotations 都可读；双栏最合理。
Fig. 6 adaptive | 6.0 x 3.4 in | 140 mm | 基本达标。建议 1.5 栏；90 mm 会使顶部两行 annotation 过挤。

所以版面上真正要做的是：不要拿现有 9-12 inch PDF/PNG 直接缩放进模板，而是在目标物理宽度下重新 render，并保持最终字体 >=约7 pt。这正是 FIG-E 时已经识别、但尚未执行的那个 production item。

两张新 PNG 目前视觉上已通过：Fig. 2 的 mathtext PFI_h(c,r) 已统一；Fig. 5 的 (b) 白字修复也确实可见。代码同样一致。

六张表：
表 | 版面建议
Table 1 Data layers | 4 列且 Source/Role 较长；建议 140-190 mm，优先 full width。Caption 完整。
Table 2 Model specifications | Configuration 列最长；建议 190 mm full width。否则会产生大量窄行换行。
Table 3 Spatial CV | 3 列、10 行；140 mm 足够。ddof=0 已集中在 Note，caption 不再重复，当前正确。
Table 4 Scale loss | 4 个短数值列，表体很紧凑；90-140 mm 均可，推荐 140 mm 以容纳长 caption。
Table 5 Adaptive counts | 2 列、3 行；适合单栏 90 mm。
Table 6 Sandy | 2 列但第一列标签较长；建议 140 mm，避免 Mean flood-risk score... 多次断行。

参考论文的 PDF-derived Markdown 显示它大量使用宽版多面板图，并把图注直接配套于 figure；你的 Fig. 2 / Fig. 5 采取宽版是合适的。

图号、文件名、正文顺序：
现在 first-mention 顺序已经修成：Fig. 1 §3.1 -> Fig. 2 §4.1 -> Fig. 3 §4.2 -> Fig. 4 §4.3 -> Fig. 5 §4.3 -> Fig. 6 §4.4。Audit 也记录了 HTML anchors 1->6。
文件对应也一致：Fig. 1 workflow_schematic / Fig. 2 spatial_maps / Fig. 3 spatial_cv_folds / Fig. 4 jaccard_by_resolution / Fig. 5 resolution_effects / Fig. 6 adaptive_ablation。
投稿上传时可保留仓库文件名，但我建议生成上传 alias：Fig1_workflow.pdf, Fig2_spatial_maps.pdf, ... Fig6_adaptive.pdf，这样编辑部不会靠文件内容猜编号。

C. Submission-package 一致性

组件 | 状态 | 处理
Abstract | 通过 | 当前约 244 words、一段式、无引用；没有必要再压。
Keywords | 通过 | 6 个，内容合适。
Highlights | 缺失 | 建议现在准备。Elsevier 官方规则是 3-5 条，每条 <=85 characters including spaces，作为单独 Highlights 文件；官方也说明它不参与编辑判断、直到 final files 阶段才必须提供。
CRediT | 未完成，投稿前 blocking | 当前仍是 [待补充]。参考论文也有完整的逐作者 CRediT。
Funding | 通过 | 标准 Elsevier wording。
Competing interest | 通过 | 已有明确 declaration。
Data/code availability | 基本通过，但存在 release-tag 不一致 | 见下。
Generative AI declaration | 内容通过 | 当前位置就在 References 前，符合 Elsevier 当前政策；建议只把标题改成官方推荐格式。
References | 总体通过，有可追溯性 polish | 编号制正常；数据/网页源建议补精确 landing page/access date。

Highlights 候选（每条 <=85 chars，避免 H3 等缩写）：
1. A hierarchical hexagonal grid unifies learning, validation and refinement
2. Public flood observations support reproducible pluvial-flood screening
3. Class-prevalence baselines change interpretation of classification performance
4. Adaptive refinement uses 57% as many cells as uniform fine-grid refinement
5. Constant synthetic rainfall yields no rainfall-conditioned discrimination

前四条即可形成一套；第五条如果希望 Highlights 同时体现证据边界，可以保留。

AI declaration：现有内容本身符合要求："used ChatGPT (OpenAI) as an editorial reviewer ... reviewed and edited ... take full responsibility..."，并且放在 References 前。建议仅把标题从 "Declaration of Generative AI and AI-assisted technologies in the writing process" 改成 Elsevier 当前推荐："Declaration of generative AI and AI-assisted technologies in the manuscript preparation process"。

Data/code availability：这里有一个真正的 package inconsistency（W8 最大 MUST-FIX）：
当前 manuscript 写："The immutable paper release is tagged paper-v1 ... the exact commit that generated all reported outputs is recorded in the accompanying audit document."
但注入 audit 明确记录：paper-v1 -> b49379c5361f...，而且把这个 tag 描述成 R21 时的最终文本。你本轮又明确说当前 master 已经到 bb5f6af，且 W6/W7 之后新增了 Fig. 2、Fig. 5、6 tables 和随后 caption/code 修复。因此：paper-v1 现在不能同时被称为"包含当前 6图6表投稿稿的 immutable release"。
不要移动已经称为 immutable 的 paper-v1。建议最终定稿后新建 submission-v1 或 paper-v2，并让 Data availability 直接指向该 tag + exact commit。
例如最小修改为："The submission version is archived under the immutable tag submission-v1; the corresponding commit and provenance of all reported outputs are recorded in the accompanying audit document."
如果你不想建新 tag，那么 manuscript 必须改成："The earlier paper-v1 tag archives the pre-W6 manuscript state; the exact submission commit is recorded in the accompanying audit document." 前者明显更干净。
版本声明则一致：audit 记录实际环境为 scikit-learn 1.8.0 / h3 4.4.2，manuscript 的 "1.8 / 4.4" 没有错误，但投稿版本可直接写精确版本号。
Manifest 描述也和 audit 一致：来源 URL、retrieval date、license/status 均有记录。
最后一个低成本 polish：References [11]-[17] 目前多为机构主页或泛化 URL。建议让它们与 DOWNLOAD_MANIFEST 中实际 landing URL 和 retrieval date 对齐，尤其 USGS Ida HWM 可以使用 audit 已记录的 DOI 10.5066/P9OMBJPQ。这不会改变任何文献论证，但会显著增强数据真实性链。

D. W7 回归确认

W7 的 4 个 MUST-FIX + 6 个 optional 均已正确落地，无科学/数值回归。
逐项确认：
§3.5 不再提前编号引用 Fig. 5；first mention 已恢复 1->6。✔
§4.1 These correlations -> This correlation。✔
§4.1 已准确写成 fractional polygon overlap / point-presence 1。✔
Fig. 5(b) (b) 已改白色，实际 PNG 可见。✔
Fig. 1 caption 已拆句，passed to diagnostics 已去掉。✔
Fig. 2 caption 已写 synthetic Ida-like，full-fit/OOF 区分压入同一句。✔
Fig. 5 caption 已改成正向 factual wording。✔
Fig. 5(a) caption 已解释 mean/extrema。✔
Fig. 2 PFI_h 已使用 mathtext；当前 PNG 标题和 colorbar 均正确。✔
Table 3 的 ddof=0 只保留在 Note，不再 caption/Note 重复。✔

W8 最终判定

科学与图表一致性：sign-off。
投稿前剩余 3 个实际 blocking / production 项：
1. 新建并锁定当前最终 submission tag，解决 paper-v1=b493... 与当前 W8 6图6表稿的不一致。
2. 完成 CRediT 作者角色，删除 [待补充] placeholder。
3. 按最终 90/140/190 mm 物理宽度重新渲染 figures，重点是 Fig. 1 和 Fig. 2，避免当前大 canvas 被版面软件缩小后字体跌破可读尺寸。

Highlights 建议现在补，但根据 Elsevier 当前官方说明，它不是编辑判断的一部分，也不必视为 initial-submission blocker。

完成这三项后，不建议再继续做科学内容或结果层面的修改。