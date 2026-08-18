# ChatGPT paste — R24 (prose/terminology sign-off after applying R23 fixes)

我已按你 R23 的意见完成 6 处小幅修改，请你逐条确认是否可接受，并做最终表述/术语 sign-off（不要大改框架）。

## 图件代码修改（figures.py，已重新渲染 PNG/PDF）

1. Fig 1 "Static predictors" 框：改为概括式 `Static predictors (terrain, flow accumulation, land cover, buildings, hydrologic proximity)`，不再读作完整列表。
2. Fig 1：`PFI_h` → 数学下标 `PFI_h`（mathtext $\mathrm{PFI}_h$）；"Adaptive refinement (PFI_h-guided → R11)" 同步。
3. Fig 1：`H3-block GroupKFold spatial CV` 下加一行 `(R7 parent blocks)`。
4. Fig 2：x 轴 `H3-block spatial CV fold` → `H3-block spatial CV`（右端还有 Mean ± SD summary 点）。
5. Fig 3：图例 `mean / max / p90` → `Mean / Maximum / P90`。

## 正文修改（manuscript.md）

6. Fig 1 caption 的 predictors 括号同步为 `elevation, slope, flow accumulation, land cover, buildings, hydrologic proximity`。
7. "open-label" 首次在 Introduction 定义：改为 `...open-label learning—that is, learning from labels derived from publicly accessible flood observations—spatially blocked evaluation...`。
8. 两处 "end-to-end" 改为 `implementation and evaluation of the framework on the stated pilot extents` / `on two Manhattan pilots`。

请确认：这些措辞/术语改动是否可接受？有没有任何一处会引入新的歧义或不一致？
