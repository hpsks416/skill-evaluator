> ⚠️ **本仓库已废弃**：内容已并入 [agent-deploy](https://github.com/hpsks416/agent-deploy) 的 skills/skill-evaluator/ 子目录，请以 agent-deploy 为准。本仓库保留仅供历史归档。

# skill-evaluator

评估一个 skill 是否真的有效。核心原则：**测量 > 反思**。本 skill 只产出可判定的事实（token、成功率、步骤数、静态缺陷），不产出「好不好」的价值判断——那个裁决永远留给人类。

## 环境依赖

- 操作系统：Windows
- 运行时：Python 3（标准库）
- 第三方软件：无（仅依赖系统自带的 PowerShell / 标准库）

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

