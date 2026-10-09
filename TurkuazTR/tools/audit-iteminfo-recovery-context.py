#!/usr/bin/env python3
# Purpose: source-backed, non-mutating provenance report for unresolved itemInfo descriptions
# Version: 1.0.0
from __future__ import annotations

import argparse
import bisect
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Translation/Renewal/SystemEN/LuaFiles514/itemInfo.lua"
RECOVERY = ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json"
PENDING = ROOT / "TurkuazTR/iteminfo-lore.pending.json"
AUDIT = ROOT / "TurkuazTR/tools/audit-iteminfo-visible.py"
ENTRY_RE = re.compile(r"^\s*\[(\d+)\]\s*=\s*\{", re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Write JSON report to an explicit path")
    args = parser.parse_args()

    spec = importlib.util.spec_from_file_location("turkuaz_recovery_audit", AUDIT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load canonical itemInfo visible-field audit")
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)

    recovery = json.loads(RECOVERY.read_text(encoding="utf-8"))["candidates"]
    pending = json.loads(PENDING.read_text(encoding="utf-8"))
    raw = SOURCE.read_text(encoding="utf-8", errors="surrogateescape")
    descriptions = audit.collect(SOURCE)["description_counter"]
    boundaries = [(match.start(), int(match.group(1))) for match in ENTRY_RE.finditer(raw)]
    offsets = [offset for offset, _ in boundaries]

    if len(set(recovery)) != len(recovery):
        raise AssertionError("Duplicate unresolved source recovery candidates")
    if pending["candidate_count"] or pending["candidates"]:
        raise AssertionError("Clean translation pending inventory is no longer zero")
    if len(recovery) != pending["source_recovery_candidate_count"]:
        raise AssertionError("Recovery report and source recovery inventory disagree")

    rows = []
    statuses = Counter()
    for source in recovery:
        found = []
        start = 0
        normalized = source if source in descriptions else source.replace('"', chr(92) + '"')
        literal = '"' + normalized + '"'
        while (pos := raw.find(literal, start)) >= 0:
            index = bisect.bisect_right(offsets, pos) - 1
            left = raw.rfind("\n", 0, pos)
            right = raw.find("\n", pos)
            if right < 0:
                right = len(raw)
            previous_line_start = raw.rfind("\n", 0, max(0, left))
            next_line_end = raw.find("\n", right + 1)
            if next_line_end < 0:
                next_line_end = len(raw)
            found.append({
                "item_id": boundaries[index][1] if index >= 0 else None,
                "line": raw.count("\n", 0, pos) + 1,
                "previous_line": raw[previous_line_start + 1:left].strip(),
                "exact_source_line": raw[left + 1:right].strip(),
                "next_line": raw[right + 1:next_line_end].strip(),
            })
            start = pos + len(literal)
        if not found:
            statuses["missing_literal_context"] += 1
        if source not in descriptions and normalized not in descriptions:
            statuses["missing_visible_description"] += 1
        flags = []
        if any(0xD800 <= ord(c) <= 0xDFFF for c in source):
            flags.append("invalid_encoding")
        if re.search(r"(?:,\s*$|\.\.\.\s*$|\b(?:the|of|and|to|from|by|for|a|an|with)\s*$)", source, re.I):
            flags.append("possibly_truncated")
        if not flags:
            flags.append("semantic_source_review")
        for flag in flags:
            statuses[flag] += 1
        rows.append({
            "source": source,
            "occurrences": descriptions.get(source, descriptions.get(normalized, 0)),
            "flags": flags,
            "contexts": found[:12],
            "context_count": len(found),
        })

    result = {
        "_file_header": {
            "purpose": "Source-evidenced report, not a Turkish translation or approved text fix",
            "version": "1.0.0",
        },
        "source_path": str(SOURCE.relative_to(ROOT)),
        "recovery_path": str(RECOVERY.relative_to(ROOT)),
        "candidate_count": len(rows),
        "status_counts": dict(sorted(statuses.items())),
        "candidates": rows,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_count": len(rows),
        "context_covered": sum(bool(row["contexts"]) for row in rows),
        "status_counts": result["status_counts"],
        "unmatched_sources": [row["source"] for row in rows if not row["contexts"]],
    }, sort_keys=True))
    if statuses["missing_literal_context"] or statuses["missing_visible_description"]:
        raise AssertionError("Source recovery candidates are not fully grounded in original itemInfo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
