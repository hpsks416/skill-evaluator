# skill-evaluator

Evaluate whether an existing skill actually helps, using static checks on its SKILL.md plus an isolated A/B test (with-skill vs without-skill) that reports only measurable facts — never a keep/delete verdict. Use when the user asks to audit, benchmark, grade, or QA a skill, or wonders whether a skill is "有没有都一样". Not for writing new skills or editing skills.

## 这是什么

DSH（DeepSeek Harness）skill —— 一个可由 AI agent 按需自动加载的能力单元。克隆到 skill 目录后，DSH 会依据上方描述自动发现并触发它，无需构建。

## 安装

最简单：用 [dsh-config](https://github.com/hpsks416/dsh-config) 的一键脚本 `install.ps1` 批量安装全部 skill。单个安装：

    # GitHub
    git clone https://github.com/hpsks416/skill-evaluator.git "$env:USERPROFILE\.dsh\skills\skill-evaluator"
    # 或 Gitee（国内直连更快）
    git clone https://gitee.com/hpsks416/skill-evaluator.git "$env:USERPROFILE\.dsh\skills\skill-evaluator"

克隆后 DSH 会自动重新发现，无需重启。更新用：

    git -C "$env:USERPROFILE\.dsh\skills\skill-evaluator" pull

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

## 依赖

脚本以 Python 3 标准库为主，无第三方依赖（个别脚本如需额外依赖，见文件头注释）。

## License

MIT License. See [LICENSE](LICENSE).
