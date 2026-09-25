---
name: skill-evaluator
description: Evaluate whether an existing skill actually helps, using static checks on its SKILL.md plus an isolated A/B test (with-skill vs without-skill) that reports only measurable facts — never a keep/delete verdict. Use when the user asks to audit, benchmark, grade, or QA a skill, or wonders whether a skill is "有没有都一样". Not for writing new skills or editing skills.
---

# Skill Evaluator

评估一个 skill 是否真的有效。核心原则：**测量 > 反思**。本 skill 只产出可判定的事实（token、成功率、步骤数、静态缺陷），不产出「好不好」的价值判断——那个裁决永远留给人类。

**理论底座**：前馈 Transformer 无法内化「对思考的思考」（元认知）——它只能模仿反思的文本，不能真正执行反思。所以评估必须外置：本 skill 是「外部元认知引擎」的**评估回路**，用可判定事实替代模型「自以为是的反思」，对标业界共识的外部 Critic/Reviser 循环，不是权宜之计。

## 何时用

- 用户问「这个 skill 好不好用 / 有没有都一样 / 值不值得留」
- 需要给 skill 库做体检、筛选、A/B 对照
- 一个新 skill 写完，想知道它是否有 Skill Lift

## 何时不用

- 写新 skill、改 skill 正文（那是编辑/架构的事，不是评估）
- 单步任务、单文件编辑（直接做）

## 铁律（违反即失效）

1. **测量，不反思**：评估结论必须来自可判定的事实（脚本输出、A/B 数据、静态检查结果），绝不来自「我觉得这个 skill 写得不错」这类自我评价。
2. **隔离评估者**：A/B 测试必须用独立 subagent 执行，评估者不能是写这个 skill 的同一个上下文——创作者给自己放水是已知的系统性偏差。
3. **只报数据，不给裁决**：最终输出只陈述事实（指标、缺陷、对比），不写「建议删除/保留」。是否删改由用户决定。
4. **不碰原文件**：评估过程 read-only，绝不修改、覆盖、删除被评估的 skill。产出物写进工作区临时目录。
5. **有界迭代**：动态 A/B 最多跑一轮对照；发现 skill 有致命静态缺陷时，报告缺陷、不尝试当场修复。

## 工作流

### 阶段 0 — 定位目标

- 用 `skillmgr_get <name>` 读取目标 skill 的完整正文（frontmatter + body）。
- 记录：name、description、正文长度、是否有 `references/`、是否有 `scripts/`、是否有 `evals.yaml`。
- 若目标不存在，停止并说明。

### 阶段 1 — 静态体检（先跑，零 token 成本）

运行 `python "<skill-dir>\scripts\static_check.py" --skill "<被评估skill的目录>"`。

脚本只读，产出结构化 JSON，检查项：

1. frontmatter 完整性（`name`、`description` 存在且非空）。
2. `name` 与目录名一致（kebab-case）。
3. `description` 是否为「何时用」而非「概括流程」（启发式：含 "Use when" / "当…时" / "适用于"）。
4. 引用的 `references/`、`scripts/` 路径是否真实存在（引用了不存在的文件 = 坏引用）。
5. 是否有 `evals.yaml`（没有则标「不可动态评估」，并降级为仅静态）。
6. 安全红旗：正文里是否出现硬编码密钥模式（`sk-`、`ghp_`、`-----BEGIN`、`password=`）。

静态结果直接进入最终报告，无需任何 LLM 判断。

### 阶段 2 — 准备 evals（动态评估的前置）

- 若目标 skill 自带 `evals.yaml`，直接采用。
- 若没有，**不自动生成**——报告「该 skill 缺少 evals，无法动态评估」，并把「补 evals」列为下一步建议。生成 evals 是另一个动作（需要人类指定「什么算成功」），不能由评估器替用户臆造成功标准。

### 阶段 3 — 隔离 A/B 对照（仅在 evals 存在时）

对 `evals.yaml` 里的每个用例，用**独立 subagent** 跑两次，参数只差「是否注入 skill 正文」：

- **A 组（with-skill）**：subagent 的 prompt 里先给完整 skill 正文，再给用例任务。
- **B 组（without-skill）**：subagent 的 prompt 里只给用例任务，不给 skill。

两组用相同的模型、相同的用例、相同的判定脚本。

**判定口径是「全过程」**：子代理的**所有输出**——运行中的中间消息（`send_message` / 中间汇报）+ 最终答复（closing message）——都要收集，拼接成一个完整文本后再跑 checks。任何一个阶段出现违禁内容（例如中间过程回显了明文 token、最终答复才脱敏），该用例判 fail。只判最终答复会漏掉「中间回显、最终收敛」的泄露。

判定：对每组拼接后的全过程文本，运行用例里声明的检查（`contains` / `not_contains` / `regex` / `json_schema`），得到 pass/fail。

记录每组的：
- 每个用例的 pass/fail
- 子代理消耗的 token（若运行时暴露 token 统计则记录；拿不到就标 `unknown`，不编造）
- 步骤数（若可观测）

### 阶段 4 — 产出数据报告

按 `references/report-schema.md` 的模板，写一份 markdown 报告到 `_skill_evaluation_report_<name>.md`，并 `present`。

报告只含：
- 静态体检结果（pass/fail 清单 + 缺陷列表）
- A/B 对照表（每用例：with-skill pass? / without-skill pass?）
- 汇总事实（如「3/3 用例 with-skill 通过，2/3 without-skill 通过」）
- 缺口清单（如「缺 evals」「坏引用」「描述是流程概括而非触发条件」）

**报告里不出现任何「建议删除/保留」的结论。** 数据摆出来，裁决交给用户。

## 边界

- 不评估「还没写出来的 skill」。
- 不替用户定义「什么算成功」——那是 evals 的职责，而 evals 由人（或用户明确委托）来写。
- A/B 只在有 evals 时跑；没有 evals 就停在静态体检，不硬造对照。
- 评估器自身也是 skill，同样遵守本规则（它自带 evals.yaml 作为示范）。

## References

- `references/evals-schema.md` — evals.yaml 的字段规范与示例。
- `references/report-schema.md` — 数据报告模板。
- `scripts/static_check.py` — 静态体检脚本（read-only，stdlib）。
