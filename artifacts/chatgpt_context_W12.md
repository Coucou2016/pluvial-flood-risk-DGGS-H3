# W12 复核请求（2026-08-20）：确认 W11 写作 humanize 落地正确、无回归、可 sign-off

## 背景
你上一轮（W11）判定稿件科学内容已 sign-off，写作风格需完成 6 个 MUST-FIX 后进入"正常 IJDRR submission manuscript"范围，并给出约 16 条建议 + 3 条可选。我方已按你的 A/B/C/D 全部落实并推送（commit `c939694`）。本轮请复核落地是否正确、有无数字/科学回归、写作风格是否可正式 sign-off。

## W11 已落实清单（请逐项核对）

### MUST-FIX（6）
1. **Abstract**：单段按 problem→method→results→boundary 重排；`demonstrates...lists everything` → `evaluates...uses H3 as the common spatial support`；`On a small Manhattan pilot` → `Under this blocked evaluation, a small Manhattan pilot`；`On a larger pilot` → `In the larger pilot`；末两句改"结果意义"（`...remain unevaluated`）。
2. **Introduction contribution paragraph**：组件清单 → "H3 hierarchy 连接科学环节"；PFI 句 → `distinct from both feature-importance measures and the H3-aggregated building index of Svellingen et al. [5]`。
3. **Research questions**：去 (i)/(ii)/(iii)，改自然连续三问；结尾 `...on a smaller and an expanded Manhattan pilot extent rather than on a citywide scale`。
4. **§4.1 去重复 disclaimer**：两句合并为 `The spatial concordance is descriptive; predictive performance is assessed separately from the out-of-fold metrics reported in Section 4.2.`
5. **§5.4 Limitations**：9 条 numbered → 3 个主题段落（所有边界与数字原样）。
6. **Conclusion**：`This study shows / The experiments demonstrate / The results indicate` 三连 → 连续论证。

### 建议（已落实，高收益）
- §2 去 `Extent./Data sources./What the labels mean./Rainfall.` 行内标签；
- Methods 加整体入口句；§3.1/3.6/3.7 防御否定 → 正向定义；
- §4.4/§4.5 否定自然化；§4.7 删中途 `still not citywide`（段末保留 `citywide generalisation remains unevaluated`）；
- §5.1 开头三项罗列 → synthesis；§5.2 Svellingen 比较改写（保留 `rather than reproducing their metric`）；§5.3 四角色句压缩；
- 引言第一段末尾加 spatial-representation bridge；H3 段结尾 `does not learn...nor does it...` → `leaving open the question...`；
- Fig.1 caption `bypasses learning` → `represents the post-fit coastal-overlap diagnostic`；Fig.2 caption `not an out-of-fold prediction` → `fitted using all 141 cells`。

### 可选（已落实）
- Highlight 5 → `Constant training rainfall produces a flat rainfall-conditioned response`；
- §5.5 Future work 去 (i)–(iv) 编号。

## 本轮注入文件（2 个）
- `chatgpt_context_W12.md`（本文件）
- `manuscript.md`（W11 更新后最新稿）

## 请回答（中文，结构化）
1. **逐项核对**：6 MUST-FIX + 建议 + 可选是否全部正确落地？有无落地偏差（例如某句改了一半、语义漂移、指代断裂）？
2. **数字回归**：复核 Abstract、§4、§5、Conclusion 中所有数字（0.784/0.866/0.683/0.861/0.642/0.525/0.703/0.723/0.808/0.893/0.167/0.977/0.988/1.000、571 of 991、3,933/6,909、56.9%/27.9×、0.030/0.343、80.1%/47.9%、0.14、0.51、0.803、n=141/956、21–49/190–193、Fold4 n=24）是否全部原样保留、无新增/删改。
3. **科学边界**：确认以下必须保留的诚实边界未被 humanize 掉：open labels ≠ verified inundation；PFI_h ≠ feature importance / PFIb；0.167 ≠ reproduction of 0.14；Sandy 不进训练；constant rainfall → flat response；pilots ≠ citywide；no separate calibration；no R11 retraining。
4. **连贯性**：引言新增 bridge 句 + gap 改写 + contribution 重写三者之间衔接是否自然、无指代断裂？
5. **最终判定**：写作风格是否已从"研究总结/答辩/AI 整理稿"进入"正常 IJDRR submission manuscript"范围？给 MUST-FIX / 建议 / sign-off 分级。若 sign-off，请明确说明"写作风格 humanize 完成"。

## 约束
- 不改变科学内容、结果、核心结论与全部数字。
- 只复核写作 humanize 落地、连贯性、边界保留。
