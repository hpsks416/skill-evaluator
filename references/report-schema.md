# 数据报告模板

skill-evaluator 的最终产出。**只陈述事实，不给「删除/保留」裁决。**

---

# Skill 评估报告：`<skill-name>`

> 评估方式：静态体检 + 隔离 A/B（若有 evals）。数据只读，未修改任何被评估文件。

## 一、静态体检

| 检查项 | 结果 | 说明 |
|---|---|---|
| frontmatter 完整 | pass / fail | 缺 `name` / `description` |
| name 与目录一致 | pass / fail | |
| description 是「何时用」 | pass / warn | 若是流程概括则 warn |
| references/scripts 引用存在 | pass / fail | 列出坏引用 |
| 含 evals.yaml | 有 / **无** | 无则不可动态评估 |
| 安全红旗 | 干净 / 命中 | 列出命中项（脱敏后） |

静态缺陷清单（若有，逐条列出）：

- `<缺陷 1>`
- `<缺陷 2>`

## 二、隔离 A/B 对照（仅当有 evals）

> 每组用独立 subagent，参数只差「是否注入 skill 正文」。模型、用例、判定脚本相同。

| 用例 | with-skill | without-skill | 判定 |
|---|---|---|---|
| success-path | pass | pass | 两组都过 → 该用例测不出增量 |
| failure-path | pass | fail | with-skill 有增量 ✅ |
| boundary | pass | pass | — |

### 汇总事实

- with-skill 通过：`x/y`
- without-skill 通过：`z/y`
- 有增量的用例数（with 过 / without 不过）：`n`
- token 消耗（若可观测）：with-skill `A` vs without-skill `B`；拿不到则标 `unknown`，不编造。

## 三、缺口清单（事实，非裁决）

- 缺 evals → 无法动态评估，建议补 `evals.yaml`。
- 描述是流程概括而非触发条件 → 影响可发现性。
- 引用了不存在的 `references/xxx.md` → 坏引用。
- 正文含硬编码密钥模式 → 高危，需立即处理（但本评估器不动它）。

---

## 报告写作纪律

1. **不出现「建议删除」「建议保留」「这个 skill 没用」等结论句。** 只摆数据。
2. 所有 pass/fail 来自脚本或判定结果，不是评估者的主观印象。
3. token/步骤数拿不到就写 `unknown`，绝不编造数字。
4. 「有增量」的判定标准是客观的：某用例 with-skill 通过且 without-skill 不通过。
