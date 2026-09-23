#!/usr/bin/env python3
"""skill-evaluator 静态体检脚本（read-only，stdlib only）。

检查一个 skill 目录的 SKILL.md 的静态质量，输出结构化 JSON。
不修改任何文件，不访问网络。
"""
import json
import re
import sys
from pathlib import Path

# kebab-case 校验（与 DSH skill name 语法一致）
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# 描述是「何时用」的启发式信号
WHEN_SIGNALS = ("use when", "when the user", "当", "适用于", "触发", "triggered")

# 硬编码密钥红旗（只用于标记，不打印匹配内容）
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"gho_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    # 只匹配「password=真实值」而非列举 `password=` 这类字面；排除占位符与空值。
    re.compile(r"password\s*=\s*[\"']?[A-Za-z0-9@#$%^&*+/_-]{8,}[\"']?", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9]{16,}[\"']?", re.IGNORECASE),
]

# 引用文件的合法前缀目录
REF_DIRS = ("references", "scripts")

# 正文尺寸棘轮（ratchet）：防 skill 膨胀。借鉴 skill-evolution 的绝对上限思路。
# 超过软阈值 warn（可读性下降），超过硬阈值 fail（应拆到 references/）。
BODY_SOFT_LIMIT = 8000    # 字符
BODY_HARD_LIMIT = 20000   # 字符


def read_skill(skill_dir: Path):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return None, f"missing SKILL.md in {skill_dir}"
    return skill_md.read_text(encoding="utf-8"), None


def parse_frontmatter(text: str):
    """返回 (frontmatter_dict, body_text)。无 frontmatter 则返回 ({}, text)。"""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).split("\n"):
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        kv = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip("\"'")
    return fm, text[m.end():]


def extract_ref_paths(body: str):
    """提取正文里形如 `references/xxx.md` 或 `scripts/xxx.py` 的引用（含完整路径）。"""
    return set(re.findall(r"(?:references|scripts)/[A-Za-z0-9_\-./]+", body))


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--skill":
        print(json.dumps({"error": "usage: static_check.py --skill <skill_dir>"}, ensure_ascii=False))
        return 1

    skill_dir = Path(sys.argv[2])
    text, err = read_skill(skill_dir)
    if err:
        print(json.dumps({"ok": False, "checks": [], "defects": [err]}, ensure_ascii=False))
        return 0

    fm, body = parse_frontmatter(text)
    checks = []
    defects = []

    # 1. frontmatter 完整性
    has_name = bool(fm.get("name"))
    has_desc = bool(fm.get("description"))
    checks.append({"check": "frontmatter_complete", "result": "pass" if (has_name and has_desc) else "fail",
                   "detail": f"name={'yes' if has_name else 'no'} description={'yes' if has_desc else 'no'}"})
    if not (has_name and has_desc):
        defects.append("frontmatter 缺少 name 或 description")

    # 2. name 与目录一致
    dir_name = skill_dir.name
    name_ok = has_name and fm["name"] == dir_name and bool(NAME_RE.match(fm["name"]))
    checks.append({"check": "name_matches_dir", "result": "pass" if name_ok else "fail",
                   "detail": f"frontmatter_name={fm.get('name')!r} dir={dir_name!r}"})
    if not name_ok:
        defects.append(f"name 与目录不一致或非 kebab-case：{fm.get('name')!r} vs {dir_name!r}")

    # 3. description 是否「何时用」
    desc_lower = (fm.get("description") or "").lower()
    when_like = any(s in desc_lower for s in WHEN_SIGNALS)
    checks.append({"check": "description_when_oriented", "result": "pass" if when_like else "warn",
                   "detail": f"contains_when_signal={when_like}"})
    if not when_like:
        defects.append("description 疑似流程概括而非「何时用」，影响可发现性")

    # 4. 引用路径存在性
    refs = extract_ref_paths(body)
    missing_refs = []
    for r in refs:
        if not (skill_dir / r).is_file():
            missing_refs.append(r)
    checks.append({"check": "references_exist", "result": "pass" if not missing_refs else "fail",
                   "detail": f"refs={sorted(refs)} missing={missing_refs}"})
    for mr in missing_refs:
        defects.append(f"引用了不存在的文件：{mr}")

    # 5. 是否有 evals
    has_evals = (skill_dir / "evals.yaml").is_file()
    checks.append({"check": "has_evals", "result": "yes" if has_evals else "no",
                   "detail": "evals.yaml exists" if has_evals else "no evals.yaml → 不可动态评估"})
    if not has_evals:
        defects.append("缺少 evals.yaml，无法做动态 A/B 评估")

    # 6. 安全红旗（只报命中数量，不打印内容）
    secret_hits = []
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            secret_hits.append(pat.pattern)
    checks.append({"check": "security_red_flags", "result": "clean" if not secret_hits else "hit",
                   "detail": f"hits={len(secret_hits)}"})
    for h in secret_hits:
        defects.append(f"正文含疑似硬编码密钥模式（已脱敏）：{h}")

    # 7. 正文尺寸棘轮（ratchet）
    body_len = len(body)
    if body_len > BODY_HARD_LIMIT:
        size_result = "fail"
        defects.append(f"正文 {body_len} 字符超过硬上限 {BODY_HARD_LIMIT}，应拆分到 references/")
    elif body_len > BODY_SOFT_LIMIT:
        size_result = "warn"
    else:
        size_result = "pass"
    checks.append({"check": "body_size_ratchet", "result": size_result,
                   "detail": f"body={body_len} chars (soft={BODY_SOFT_LIMIT}, hard={BODY_HARD_LIMIT})"})

    result = {
        "ok": True,
        "skill": fm.get("name", dir_name),
        "body_length_chars": len(body),
        "checks": checks,
        "defects": defects,
        "summary": {
            "pass": sum(1 for c in checks if c["result"] == "pass"),
            "warn": sum(1 for c in checks if c["result"] == "warn"),
            "fail": sum(1 for c in checks if c["result"] == "fail"),
            "defect_count": len(defects),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
