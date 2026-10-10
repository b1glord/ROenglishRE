#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/audit-iteminfo-recovery-context.py
# 📌 Amac: Kurtarilamayan itemInfo kaynaklarini kimlik ve risk sinifina gore denetler
# 📌 Modul - Tool Python
# Version: 1.8.0
# Aciklama: v1.164.0 alti kanitli onarim ve bitisik satir muhasebesi
# Bagimli Oldugu Katman: Tool
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



def source_integrity_flags(source: str) -> list[str]:
    """Triage hints only; never invent missing gameplay numbers or source text."""
    flags = []
    if any(0xDC80 <= ord(ch) <= 0xDCFF for ch in source):
        flags.append("invalid_source_bytes")
    if re.search(r"\^[0-9a-fA-F]{6}\^000000", source):
        flags.append("empty_color_span")
    if re.search(r"\b(?:by|of)\s*%", source, flags=re.IGNORECASE):
        flags.append("missing_percent_value")
    if re.search(r"\^[0-9a-fA-F]{5}[a-fA-F](?=[a-z])", source):
        flags.append("suspected_color_marker_text_overlap")
    if re.search(r"\^[0-9a-fA-F]{6}\+\s*or\s+higher", source, flags=re.IGNORECASE):
        flags.append("missing_refine_threshold")
    return flags


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
        # A PR translating source-recovery fragments updates the canonical
        # quarantine first; regenerated pending summaries are committed by
        # the post-merge localization workflow. Do not weaken the inventory
        # check without source-specific proof of exactly that delta.
        delta = pending["source_recovery_candidate_count"] - len(recovery)
        proven = False
        for version in ("1164", "1163", "1162", "1161", "1160", "1158", "1157"):
            evidence_path = ROOT / f"TurkuazTR/config/iteminfo-recovery-evidence-v{version}.json"
            shard_path = ROOT / f"TurkuazTR/config/iteminfo-exact-v{version}.tr.json"
            if not evidence_path.exists() or not shard_path.exists():
                continue
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            shard = json.loads(shard_path.read_text(encoding="utf-8"))["translations"]
            resolved = {entry["source"] for entry in evidence["entries"]}
            companions = {
                entry["adjacent_source"]
                for entry in evidence["entries"]
                if entry.get("adjacent_source") and not entry.get("adjacent_translation_path")
            }
            if (
                delta > 0
                and len(resolved) == delta
                and len(resolved) == evidence["resolved_count"]
                and resolved.union(companions) == set(shard)
                and not resolved.intersection(recovery)
                and (version != "1160" or len(companions) == evidence["adjacent_translation_count"])
            ):
                proven = True
                break
        if not proven:
            raise AssertionError("Unexplained recovery inventory drift in PR")

    rows = []
    statuses = Counter()
    source_risks = Counter()
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
        detected = source_integrity_flags(source)
        source_risks.update(detected)
        rows.append({
            "source": source,
            "integrity_flags": detected,
            "triage_priority": "source_repair_required" if detected else "semantic_upstream_review",
            "occurrences": descriptions.get(source, descriptions.get(normalized, 0)),
            "flags": flags,
            "contexts": found[:12],
            "context_count": len(found),
        })

    result = {
        "_file_header": {
            "purpose": "Source-evidenced report, not a Turkish translation or approved text fix",
            "version": "1.1.0",
        },
        "source_path": str(SOURCE.relative_to(ROOT)),
        "recovery_path": str(RECOVERY.relative_to(ROOT)),
        "candidate_count": len(rows),
        "status_counts": dict(sorted(statuses.items())),
        "integrity_risk_counts": dict(sorted(source_risks.items())),
        "high_risk_candidate_count": sum(bool(row["integrity_flags"]) for row in rows),
        "candidates": rows,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_count": len(rows),
        "context_covered": sum(bool(row["contexts"]) for row in rows),
        "status_counts": result["status_counts"],
        "integrity_risk_counts": result["integrity_risk_counts"],
        "high_risk_candidate_count": result["high_risk_candidate_count"],
        "unmatched_sources": [row["source"] for row in rows if not row["contexts"]],
    }, sort_keys=True))
    if statuses["missing_literal_context"] or statuses["missing_visible_description"]:
        raise AssertionError("Source recovery candidates are not fully grounded in original itemInfo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
