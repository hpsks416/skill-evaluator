# skill-evaluator

评估一个 skill 是否真的有效。核心原则：**测量 > 反思**。本 skill 只产出可判定的事实（token、成功率、步骤数、静态缺陷），不产出「好不好」的价值判断——那个裁决永远留给人类。

## 适用对象

- DeepSeek Harness（DSH）用户：一个可由 AI agent 按需自动加载的 skill，克隆即用、无需构建。
- 需要评估 skill 是否真的有效的人

## 目录结构

    skill-evaluator/
    ├── SKILL.md    技能入口与工作流
    ├── evals.yaml
    ├── references\evals-schema.md
    ├── references\report-schema.md
    ├── scripts\dedup_check.py
    ├── scripts\judge.py
    ├── scripts\static_check.py
    ├── scripts\token_cost.py

## 安装

    # GitHub
    git clone https://github.com/hpsks416/skill-evaluator.git "$env:USERPROFILE\.dsh\skills\skill-evaluator"
    # 或 Gitee（国内直连）
    git clone https://gitee.com/hpsks416/skill-evaluator.git "$env:USERPROFILE\.dsh\skills\skill-evaluator"

克隆后 DSH 自动重新发现，无需构建。

## License

MIT License. See [LICENSE](LICENSE).
