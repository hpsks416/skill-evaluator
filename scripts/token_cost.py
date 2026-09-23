#!/usr/bin/env python3
"""估算 skill 的三层 token 消耗（read-only，stdlib only）。

借鉴 tokc 的三层计费模型，但针对 DSH（非 Claude Code）：
  T1 常驻税 = frontmatter 的 name + description，随 skill 目录每次注入
  T2 正文   = SKILL.md body，每次调用加载一次
  T3 按需   = references/、scripts/，只在读文件时计

用法:
  python token_cost.py --skill <skill目录> [--invocations 3] [--sessions 1]

输出三层各自的 token 估算 + 脚本化收益 + 是否值得脚本化 + 优先级建议。
"""
import json
import re
import sys
from pathlib import Path


def parse_frontmatter(text: str):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).split("\n"):
        kv = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line.rstrip())
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip("\"'")
    return fm, text[m.end():]


def estimate_tokens(text: str) -> int:
    """估算 token：中文每 2 字符 1 token，其它每 4 字符 1 token。"""
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    other = len(text) - cjk
    return int(cjk / 2 + other / 4)


def main():
    args = sys.argv[1:]
    skill_dir = None
    invocations = 3   # 预计被调用次数（T2 计费次数）
    sessions = 1      # 预计会话数（T1 常驻税计费次数）
    i = 0
    while i < len(args):
        if args[i] == "--skill" and i + 1 < len(args):
            skill_dir = Path(args[i + 1]); i += 2
        elif args[i] == "--invocations" and i + 1 < len(args):
            invocations = int(args[i + 1]); i += 2
        elif args[i] == "--sessions" and i + 1 < len(args):
            sessions = int(args[i + 1]); i += 2
        else:
            i += 1
    if skill_dir is None:
        print(json.dumps({"error": "usage: token_cost.py --skill <dir> [--invocations 3] [--sessions 1]"}, ensure_ascii=False))
        return 1

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print(json.dumps({"error": "SKILL.md not found"}, ensure_ascii=False))
        return 1
    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    # T1 常驻税：name + description（每次请求都发，最贵）
    name = fm.get("name", "")
    desc = fm.get("description", "")
    t1_text = name + " " + desc
    t1_tokens = estimate_tokens(t1_text)
    t1_total = t1_tokens * sessions

    # T2 正文：每次调用加载一次
    t2_tokens = estimate_tokens(body)
    t2_total = t2_tokens * invocations

    # T3 按需：references/scripts 文件（只在读时计，不计入常驻）
    t3_tokens = 0
    t3_files = 0
    for sub in ("references", "scripts"):
        d = skill_dir / sub
        if d.is_dir():
            for f in d.rglob("*"):
                if f.is_file():
                    try:
                        t3_tokens += estimate_tokens(f.read_text(encoding="utf-8"))
                        t3_files += 1
                    except Exception:
                        pass

    # 脚本化收益：T2 的确定性逻辑外化后，从整段正文降为「一句命令+读 JSON」≈50 token
    scripted_per_call = 50
    saved_per_call = max(0, t2_tokens - scripted_per_call)
    saved_total = saved_per_call * invocations

    # 判定
    t1_bloated = t1_tokens > 250
    worth_scripting = t2_tokens > 2000 and saved_per_call > 200

    result = {
        "skill": name or skill_dir.name,
        "tiers": {
            "T1_always_on": {"tokens": t1_tokens, "charged_sessions": sessions, "total": t1_total,
                             "bloated": t1_bloated},
            "T2_body": {"tokens": t2_tokens, "charged_invocations": invocations, "total": t2_total},
            "T3_on_demand": {"tokens": t3_tokens, "files": t3_files, "note": "按需计，不计常驻"},
        },
        "scripting": {
            "saved_per_call": saved_per_call,
            "saved_total": saved_total,
            "worth_scripting": worth_scripting,
        },
        "priority": [],
    }
    if t1_bloated:
        result["priority"].append("T1 描述臃肿（>250 token），先精简 description")
    if worth_scripting:
        result["priority"].append("T2 正文大且复用高，值得脚本化迁移")
    if not result["priority"]:
        result["priority"].append("成本可接受，无需优化")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
