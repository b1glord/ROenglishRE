#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/sync-iteminfo-manifest.py
# 📌 Amac: Guncel itemInfo exact, pending ve source-recovery metriklerini manifest ile eslestirir
# 📌 Modul - Tool Python
# Version: 1.0.0
# Aciklama: Generated raporlardan sayilari turetir; test release snapshot metriklerini degistirmez
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "TurkuazTR/manifest.yml"


def read_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def replace_integer(contents: str, key: str, value: int) -> str:
    # Only current item_info metrics, never test_release snapshot counters.
    expression = re.compile(r"(?m)^(    " + re.escape(key) + r": )\d+$")
    if len(expression.findall(contents)) != 1:
        raise ValueError(f"Expected one itemInfo metric: {key}")
    return expression.sub(lambda match: match.group(1) + str(value), contents)


def sync_manifest(contents: str) -> tuple[str, dict[str, int]]:
    main = read_json("TurkuazTR/iteminfo-exact.tr.json")["translations"]
    final = read_json("TurkuazTR/config/iteminfo-exact-final.tr.json")["translations"]
    pending = read_json("TurkuazTR/iteminfo-lore.batch.json")
    recovery = read_json("TurkuazTR/iteminfo-lore.source-recovery.json")["candidates"]

    overlap = main.keys() & final.keys()
    if overlap:
        raise ValueError(f"Exact shards overlap on {len(overlap)} source keys")

    metrics = {
        "exact_translation_entries": len(main),
        "final_exact_translation_entries": len(final),
        "total_exact_translation_entries": len(main) + len(final),
        "lore_source_recovery_candidates": len(recovery),
        "last_generated_lore_pending_candidates": pending["remaining_candidate_count"],
        "last_generated_lore_pending_occurrences": pending["remaining_candidate_occurrences"],
    }
    if metrics["last_generated_lore_pending_candidates"] < 0:
        raise ValueError("Pending candidate count cannot be negative")
    if metrics["last_generated_lore_pending_occurrences"] < metrics["last_generated_lore_pending_candidates"]:
        raise ValueError("Pending occurrences cannot be below candidate count")

    updated = contents
    for name, count in metrics.items():
        updated = replace_integer(updated, name, count)

    note = (
        f"Generated exact primary {metrics['exact_translation_entries']}, "
        f"final {metrics['final_exact_translation_entries']}, "
        f"total {metrics['total_exact_translation_entries']}; "
        f"pending {metrics['last_generated_lore_pending_candidates']} unique / "
        f"{metrics['last_generated_lore_pending_occurrences']} occurrence; "
        f"source-recovery {metrics['lore_source_recovery_candidates']}. "
        "Tam item audit onceki checkpoint verisidir."
    )
    note_pattern = re.compile(r'(?m)^(    last_validated_metrics_note: )".*"$')
    if len(note_pattern.findall(updated)) != 1:
        raise ValueError("Expected exactly one itemInfo metrics note")
    updated = note_pattern.sub(
        lambda match: match.group(1) + json.dumps(note, ensure_ascii=True),
        updated,
    )
    return updated, metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    original = MANIFEST.read_text(encoding="utf-8")
    updated, metrics = sync_manifest(original)
    if args.check:
        if original != updated:
            raise SystemExit("itemInfo manifest is stale; run sync-iteminfo-manifest.py")
    elif updated != original:
        MANIFEST.write_text(updated, encoding="utf-8")
    print(json.dumps({"changed": original != updated, "metrics": metrics}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
