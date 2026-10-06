#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/validate-pettalk-recovery.py
# 📌 Amac: pettalk temiz ASCII havuzunda cevrilmeyen her ifadenin source-recovery envanterinde birebir bulunmasini dogrular
# 📌 Tool - Python
# Version: 1.0.0
# Aciklama: Pending readable ASCII havuzu, exact-source Turkce patch ve recovery listesi arasinda deterministik kapanis kontrati uygular
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PENDING = REPO_ROOT / "TurkuazTR/pettalktable.pending.json"
PATCH = REPO_ROOT / "TurkuazTR/pettalktable.tr.json"
RECOVERY = REPO_ROOT / "TurkuazTR/pettalktable.source-recovery.json"

TEXT_RE = re.compile(r">([^<]*)</")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_text(row: dict) -> str:
    match = TEXT_RE.search(row["source_en"])
    if not match:
        raise ValueError(f"Pet patch source_en metni ayrisamadi: {row['source_en']!r}")
    return match.group(1).strip()


def canonical(row: dict) -> tuple:
    return (
        row["text"],
        int(row["first_line"]),
        int(row["count"]),
        tuple(sorted(row.get("tags", []))),
    )


def main() -> int:
    pending = load(PENDING)
    patch = load(PATCH)
    recovery = load(RECOVERY)

    readable = pending["groups"]["readable_ascii"]
    translated = {source_text(row) for row in patch["patches"].values()}
    remaining = [row for row in readable if row["text"] not in translated]

    expected = sorted(canonical(row) for row in remaining)
    actual = sorted(canonical(row) for row in recovery["candidates"])

    if expected != actual:
        expected_set = set(expected)
        actual_set = set(actual)
        missing = sorted(expected_set - actual_set)[:20]
        stale = sorted(actual_set - expected_set)[:20]
        raise SystemExit(
            "pettalk recovery mismatch: "
            f"remaining={len(expected)} recovery={len(actual)} "
            f"missing={missing!r} stale={stale!r}"
        )

    expected_nodes = sum(row["count"] for row in remaining)
    if recovery["candidate_count"] != len(remaining):
        raise SystemExit(
            f"candidate_count mismatch: {recovery['candidate_count']} != {len(remaining)}"
        )
    if recovery["candidate_nodes"] != expected_nodes:
        raise SystemExit(
            f"candidate_nodes mismatch: {recovery['candidate_nodes']} != {expected_nodes}"
        )

    print(
        "pettalk recovery OK: "
        f"translated_unique={len(translated)} "
        f"recovery_unique={len(remaining)} "
        f"recovery_nodes={expected_nodes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
