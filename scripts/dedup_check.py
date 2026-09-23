#!/usr/bin/env python3
"""skill 相似度去重检查（read-only，stdlib only）。

扫描一个 skill 库目录下所有 SKILL.md 的 description，用词重叠（Jaccard）
找出描述高度相似的 skill 对，帮助在建新 skill 前查重、避免重复造轮子。

用法:
  python dedup_check.py --skills <skill库根目录> [--threshold 0.35]

输出: 相似度超过阈值的 skill 对列表（name1, name2, jaccard, 重叠词）。
不上向量库，纯 stdlib 词袋 + Jaccard。
"""
import json
import re
import sys
from pathlib import Path


def parse_frontmatter(text: str):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        kv = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line.rstrip())
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip("\"'")
    return fm


def tokenize(text: str):
    """词袋：小写后按非字母数字切分，去掉停用词和超短词。"""
    STOP = {"use", "when", "the", "a", "an", "to", "for", "of", "and", "or", "in",
            "on", "with", "that", "this", "is", "are", "not", "it", "as", "by",
            "from", "skill", "skills", "user", "agent", "you"}
    words = re.findall(r"[a-z0-9\u4e00-\u9fff]+", text.lower())
    return {w for w in words if w not in STOP and len(w) >= 2}


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def scan_skills(root: Path):
    """返回 [(name, description)]，跳过无法解析的。"""
    out = []
    for skill_dir in sorted(root.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            text = skill_md.read_text(encoding="utf-8")
        except Exception:
            continue
        fm = parse_frontmatter(text)
        name = fm.get("name") or skill_dir.name
        desc = fm.get("description") or ""
        if desc:
            out.append((name, desc))
    return out


def main():
    args = sys.argv[1:]
    root = None
    threshold = 0.35
    i = 0
    while i < len(args):
        if args[i] == "--skills" and i + 1 < len(args):
            root = Path(args[i + 1]); i += 2
        elif args[i] == "--threshold" and i + 1 < len(args):
            threshold = float(args[i + 1]); i += 2
        else:
            i += 1
    if root is None:
        print(json.dumps({"error": "usage: dedup_check.py --skills <dir> [--threshold 0.35]"}, ensure_ascii=False))
        return 1

    skills = scan_skills(root)
    pairs = []
    n = len(skills)
    for a in range(n):
        ta = tokenize(skills[a][1])
        for b in range(a + 1, n):
            tb = tokenize(skills[b][1])
            score = jaccard(ta, tb)
            if score >= threshold:
                pairs.append({
                    "skill1": skills[a][0],
                    "skill2": skills[b][0],
                    "jaccard": round(score, 3),
                    "overlap_words": sorted(ta & tb),
                })

    pairs.sort(key=lambda p: -p["jaccard"])
    print(json.dumps({"total_skills": n, "threshold": threshold, "similar_pairs": pairs},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
