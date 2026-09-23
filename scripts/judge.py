#!/usr/bin/env python3
"""判定 A/B 测试输出是否通过 evals 里的 checks，并量化 Skill Lift。

单文件模式（判定一组输出）：
  python judge.py <output.txt> <checks.json>

A/B 对比模式（量化 lift）：
  python judge.py compare <with_skill.txt> <without_skill.txt> <checks.json>

checks.json 形如:
  [{"type":"contains","value":"***"},{"type":"not_contains","value":"sk-..."}]

lift = with_skill 通过率 − without_skill 通过率（按用例数归一）
verdict 阈值（借鉴 skill-ab-eval）：
  ≥ +0.20   clear positive
  +0.05~+0.20 marginal
  −0.05~+0.05 no measurable effect (dead weight)
  ≤ −0.05   negative
"""
import json
import re
import sys


def run_checks(text: str, checks: list) -> dict:
    results = []
    for c in checks:
        t = c.get("type")
        passed = False
        if t == "contains":
            passed = c.get("value", "") in text
        elif t == "not_contains":
            passed = c.get("value", "") not in text
        elif t == "regex":
            passed = bool(re.search(c.get("pattern", ""), text))
        elif t == "not_regex":
            passed = not re.search(c.get("pattern", ""), text)
        elif t == "json_schema":
            try:
                obj = json.loads(text)
                req = c.get("schema", {}).get("required", [])
                passed = all(k in obj for k in req)
            except Exception:
                passed = False
        else:
            passed = False
        results.append({"type": t, "passed": passed, "expected": c})
    return {"passed": all(r["passed"] for r in results), "results": results}


def verdict(lift: float) -> str:
    if lift >= 0.20:
        return "clear positive"
    if lift >= 0.05:
        return "marginal"
    if lift > -0.05:
        return "no measurable effect"
    return "negative"


def compare(with_text: str, without_text: str, checks: list) -> dict:
    """对比两组输出，量化 lift。checks 是单一用例的检查列表。"""
    a = run_checks(with_text, checks)
    b = run_checks(without_text, checks)
    with_rate = 1.0 if a["passed"] else 0.0
    without_rate = 1.0 if b["passed"] else 0.0
    lift = with_rate - without_rate
    return {
        "with_skill": {"passed": a["passed"], "results": a["results"]},
        "without_skill": {"passed": b["passed"], "results": b["results"]},
        "with_rate": with_rate,
        "without_rate": without_rate,
        "lift": lift,
        "verdict": verdict(lift),
    }


def main():
    args = sys.argv[1:]
    if len(args) >= 1 and args[0] == "compare":
        if len(args) < 4:
            print(json.dumps({"error": "usage: judge.py compare <with.txt> <without.txt> <checks.json>"}, ensure_ascii=False))
            return 1
        with open(args[1], encoding="utf-8") as f:
            with_text = f.read()
        with open(args[2], encoding="utf-8") as f:
            without_text = f.read()
        with open(args[3], encoding="utf-8") as f:
            checks = json.load(f)
        print(json.dumps(compare(with_text, without_text, checks), ensure_ascii=False, indent=2))
        return 0

    if len(args) < 2:
        print(json.dumps({"error": "usage: judge.py <output.txt> <checks.json>  or  judge.py compare <with> <without> <checks>"}, ensure_ascii=False))
        return 1
    with open(args[0], encoding="utf-8") as f:
        text = f.read()
    with open(args[1], encoding="utf-8") as f:
        checks = json.load(f)
    print(json.dumps(run_checks(text, checks), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
