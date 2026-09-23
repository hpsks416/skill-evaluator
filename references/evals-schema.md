# evals.yaml 规范

`evals.yaml` 是一个 skill 的「可证伪验收测试」。没有它，skill 就无法做动态 A/B 评估——因为「什么算成功」没有客观定义。

## 字段规范

```yaml
# skill 名称（kebab-case，须与 SKILL.md frontmatter 的 name 一致）
skill: secret-scan
# 本文件语义版本（改动用例就 bump）
version: 1

# 至少 1 个成功路径、1 个失败路径、1 个边界条件
cases:
  - id: success-path            # 唯一 id，kebab-case
    description: 正常扫描并报告脱敏结果
    task: "检查我的项目有没有泄露的 token"   # 喂给 subagent 的任务指令
    checks:                     # 判定该用例是否通过的检查，全部满足才 pass
      - type: contains
        value: "***"            # 输出里必须出现脱敏标记
      - type: not_contains
        value: "ghp_"           # 输出里绝不能出现明文 token 前缀
      - type: regex
        pattern: "token|密钥|泄露|发现"   # 输出应命中相关语义
        # 注：regex 用 JS 正则语法（Python 的 re 与 JS 有差异，统一用 JS）

  - id: failure-path
    description: 无凭据时应报告干净
    task: "检查这个空项目有没有密钥"
    checks:
      - type: not_contains
        value: "发现泄露"        # 空项目不应报告发现

  - id: boundary-empty-input
    description: 空输入应优雅处理
    task: ""                    # 故意给空任务
    checks:
      - type: contains
        value: "?"              # 应反问澄清，而不是崩溃或瞎猜
```

## check 类型

| type | 含义 | 必填字段 |
|---|---|---|
| `contains` | 输出必须包含该字符串 | `value` |
| `not_contains` | 输出不得包含该字符串 | `value` |
| `regex` | 输出必须匹配正则 | `pattern` |
| `not_regex` | 输出不得匹配正则 | `pattern` |
| `json_schema` | 输出必须是 JSON 且通过 schema | `schema`（对象） |

检查是「与」关系：一个用例的所有 check 都通过才算 pass。

## 判定口径：全过程，而非最终答复

checks 作用的对象是子代理的**全过程输出**——中间消息（推理过程、中间汇报）+ 最终答复，拼接成一个文本后再判定。**不是只看最终答复。**

原因：模型常「中间回显、最终收敛」。例如无 skill 的 agent 检查密钥时，推理过程可能把明文 token 写出来（它"认出是假值"所以放心写），最终答复又换成 `***`。如果只判最终答复，`not_contains` 会误判为 pass，漏掉真正的泄露。

所以 `not_contains` 这类「禁则」必须覆盖全过程；`contains` 这类「应有」则可只看最终答复（中间过程本就该包含最终答复的内容）。默认一律按全过程判定，除非用例显式声明只看最终答复。

## 写 evals 的纪律

1. **成功标准必须可判定**：`contains`/`not_contains`/`regex` 是最可靠的。避免「输出要有帮助性」这种不可判定的描述——那无法自动化。
2. **至少三类各一条**：成功、失败、边界。只有成功路径的 evals 是自欺。
3. **失败路径要真的可能失败**：构造一个「正常但不该成功」的输入（空项目、无权限、缺参数）。
4. **边界要测鲁棒性**：空输入、超长输入、特殊字符路径、无网络等。
5. **不测「模型已内化的能力」**：如果你发现「无 skill 也能 pass 这个用例」，说明这个用例测不出 skill 的增量——应该改成更依赖 skill 专属内容的任务。

## 反例（不要这样写）

```yaml
# 反例：不可判定的成功标准
- id: bad
  task: "帮我做点事"
  checks:
    - type: contains
      value: "好"              # 太宽泛，无 skill 也会说"好"
```

## 正例（测 skill 的增量）

skill 的专属约束应该体现在 task 或 checks 里。例如 secret-scan 的核心价值是「脱敏」，所以 checks 必须测 `not_contains` 明文 token + `contains` 脱敏标记——这正是「无 skill 时模型容易直接回显 token」的增量点。
