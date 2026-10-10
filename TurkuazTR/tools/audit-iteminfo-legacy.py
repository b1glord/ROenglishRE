#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/audit-iteminfo-legacy.py
# 📌 Amac: Guncel itemInfo.lua ile eski Turkce arsiv dalini item ID ve gorunur alan bazinda karsilastirip geri kazanilabilir ceviri kapsamini olcer
# 📌 Tool - Python
# Version: 1.1.0
# Aciklama: Eski itemInfo satirlarini 65 source-recovery kaydi icin item-ID, komsuluk ve sayisal/renk butunluguyle denetler
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = "Translation/Renewal/SystemEN/LuaFiles514/itemInfo.lua"
LEGACY_REF = "origin/archive-tr-2025-10-25"

ENTRY_RE = re.compile(r"^\s*\[(\d+)\]\s*=\s*\{")
FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*)$")
STRING_RE = re.compile(r'"((?:\\.|[^"\\])*)"')

VISIBLE_FIELDS = {
    "unidentifiedDisplayName",
    "unidentifiedDescriptionName",
    "identifiedDisplayName",
    "identifiedDescriptionName",
}


def read_current() -> bytes:
    return (REPO_ROOT / SOURCE_PATH).read_bytes()


def read_ref(ref: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{ref}:{SOURCE_PATH}"],
        cwd=REPO_ROOT,
    )


def parse_visible(raw: bytes) -> dict[int, dict[str, tuple[str, ...]]]:
    text = raw.decode("utf-8", errors="surrogateescape")
    rows: dict[int, dict[str, tuple[str, ...]]] = {}

    current_item: int | None = None
    active_field: str | None = None
    values: list[str] = []
    brace_depth = 0

    for line in text.splitlines():
        entry = ENTRY_RE.match(line)
        if entry:
            current_item = int(entry.group(1))

        field_match = FIELD_RE.match(line)
        if field_match:
            field, value = field_match.groups()
            if field in VISIBLE_FIELDS and current_item is not None:
                active_field = field
                values = STRING_RE.findall(value)
                brace_depth = value.count("{") - value.count("}")
                if brace_depth <= 0:
                    rows.setdefault(current_item, {})[field] = tuple(values)
                    active_field = None
                    values = []
                    brace_depth = 0
            else:
                active_field = None
                values = []
                brace_depth = 0
            continue

        if active_field is not None and current_item is not None:
            values.extend(STRING_RE.findall(line))
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                rows.setdefault(current_item, {})[active_field] = tuple(values)
                active_field = None
                values = []
                brace_depth = 0

    return rows


def has_turkish_chars(values: tuple[str, ...]) -> bool:
    joined = "\n".join(values)
    return any(char in joined for char in "çÇğĞıİöÖşŞüÜ")


def safe_sample(values: tuple[str, ...], limit: int = 2) -> list[str]:
    return [value[:180] for value in values[:limit]]



COLOR_RE = re.compile(r"\^[0-9a-fA-F]{6}")
NUMBER_RE = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?")
TURKISH_TOKEN_RE = re.compile(
    r"\b(?:bir|bu|icin|olan|ile|ve|olarak|gibi|kullan|kullanilir|"
    r"artirir|azaltir|arttirir|kazanilir|esya|beceri|karakter|"
    r"saldi|dusman|olasilik|sans|saldiri|hasar|seviye|tarafindan)\b",
    re.IGNORECASE,
)
IDENTITY_FIELDS = {"identifiedDescriptionName", "unidentifiedDescriptionName"}
RECOVERY_PATH = REPO_ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json"


def number_tokens(text: str) -> Counter[str]:
    return Counter(NUMBER_RE.findall(COLOR_RE.sub("", text)))


def color_tokens(text: str) -> Counter[str]:
    return Counter(COLOR_RE.findall(text))


def probable_turkish(text: str) -> bool:
    return has_turkish_chars((text,)) or bool(TURKISH_TOKEN_RE.search(text))


def source_recovery_legacy_report(
    current: dict[int, dict[str, tuple[str, ...]]],
    legacy: dict[int, dict[str, tuple[str, ...]]],
) -> dict[str, Any]:
    """Evidence only: archive text never becomes an approved translation automatically."""
    sources = json.loads(RECOVERY_PATH.read_text(encoding="utf-8"))["candidates"]
    indexed: dict[str, list[tuple[int, str, int, tuple[str, ...]]]] = defaultdict(list)
    for item_id, fields in current.items():
        for field in IDENTITY_FIELDS:
            values = fields.get(field, ())
            for pos, value in enumerate(values):
                if value in sources:
                    indexed[value].append((item_id, field, pos, values))

    statuses: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for source in sources:
        contexts = []
        for item_id, field, pos, current_values in indexed.get(source, []):
            old = legacy.get(item_id, {})
            old_values = old.get(field, ())
            value = old_values[pos] if pos < len(old_values) else None
            same_length = len(current_values) == len(old_values)
            previous_agrees = (
                pos > 0 and pos - 1 < len(old_values)
                and current_values[pos - 1] == old_values[pos - 1]
            )
            next_agrees = (
                pos + 1 < len(current_values) and pos + 1 < len(old_values)
                and current_values[pos + 1] == old_values[pos + 1]
            )
            aligns = same_length and (previous_agrees or next_agrees)
            if item_id not in legacy:
                category = "old_item_absent"
            elif not old_values or value is None:
                category = "old_field_or_position_absent"
            elif value == source:
                category = "same_source_untranslated"
            elif not aligns:
                category = "unaligned_manual_review"
            elif probable_turkish(value):
                category = "old_turkish_candidate"
            else:
                category = "old_different_text"
            numeric_safe = value is not None and number_tokens(source) == number_tokens(value)
            color_safe = value is not None and color_tokens(source) == color_tokens(value)
            statuses[category] += 1
            contexts.append({
                "item_id": item_id,
                "field": field,
                "line_index": pos,
                "current_lines": len(current_values),
                "old_lines": len(old_values),
                "old_value": value,
                "category": category,
                "numeric_safe": numeric_safe,
                "color_safe": color_safe,
                "same_length": same_length,
                "previous_line_exact": previous_agrees,
                "next_line_exact": next_agrees,
                "current_previous": current_values[pos - 1] if pos > 0 else None,
                "old_previous": old_values[pos - 1] if pos > 0 and pos - 1 < len(old_values) else None,
                "current_next": current_values[pos + 1] if pos + 1 < len(current_values) else None,
                "old_next": old_values[pos + 1] if pos + 1 < len(old_values) else None,
            })
        if not contexts:
            statuses["no_current_context"] += 1
        rows.append({
            "source": source,
            "current_occurrences": len(contexts),
            "contexts": contexts,
            "reviewable": any(c["category"] == "old_turkish_candidate" for c in contexts),
            "direct_numeric_color_match": any(
                c["category"] == "old_turkish_candidate"
                and c["numeric_safe"] and c["color_safe"]
                for c in contexts
            ),
        })
    return {
        "_file_header": {
            "path": "/ROenglishRE/TurkuazTR/reports/iteminfo-legacy-recovery.json",
            "purpose": "Read-only comparison of quarantined current descriptions to 2025 archive",
            "module": "Source Comparison - JSON",
            "version": "1.0.0",
            "description": "Candidate inventory and provenance; not automatic translation approval",
            "dependency_layer": "Tool",
        },
        "source_path": SOURCE_PATH,
        "legacy_ref": LEGACY_REF,
        "recovery_count": len(sources),
        "matched_source_count": sum(bool(row["contexts"]) for row in rows),
        "old_turkish_source_count": sum(row["reviewable"] for row in rows),
        "direct_numeric_color_source_count": sum(row["direct_numeric_color_match"] for row in rows),
        "context_categories": dict(sorted(statuses.items())),
        "candidates": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--recovery-report", type=Path, help="Write read-only archived-translation matching evidence")
    args = parser.parse_args()

    current = parse_visible(read_current())
    legacy = parse_visible(read_ref(LEGACY_REF))

    if args.recovery_report:
        report = source_recovery_legacy_report(current, legacy)
        args.recovery_report.parent.mkdir(parents=True, exist_ok=True)
        args.recovery_report.write_text(
            json.dumps(report, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        print("legacy_recovery_report=" + json.dumps({
            "recovery_count": report["recovery_count"],
            "matched_source_count": report["matched_source_count"],
            "old_turkish_source_count": report["old_turkish_source_count"],
            "direct_numeric_color_source_count": report["direct_numeric_color_source_count"],
            "context_categories": report["context_categories"],
        }, sort_keys=True))

    common_ids = sorted(set(current) & set(legacy))
    equal_fields = 0
    changed_fields = 0
    legacy_only_fields = 0
    current_only_fields = 0
    changed_with_turkish = 0
    changed_items: set[int] = set()
    samples: list[dict[str, object]] = []

    for item_id in common_ids:
        current_fields = current[item_id]
        legacy_fields = legacy[item_id]
        for field in sorted(VISIBLE_FIELDS):
            current_value = current_fields.get(field)
            legacy_value = legacy_fields.get(field)

            if current_value is None and legacy_value is None:
                continue
            if current_value is None:
                legacy_only_fields += 1
                continue
            if legacy_value is None:
                current_only_fields += 1
                continue
            if current_value == legacy_value:
                equal_fields += 1
                continue

            changed_fields += 1
            changed_items.add(item_id)
            if has_turkish_chars(legacy_value):
                changed_with_turkish += 1

            if len(samples) < 24:
                samples.append(
                    {
                        "item_id": item_id,
                        "field": field,
                        "current": safe_sample(current_value),
                        "legacy": safe_sample(legacy_value),
                        "legacy_has_turkish_chars": has_turkish_chars(legacy_value),
                    }
                )

    payload = {
        "source_path": SOURCE_PATH,
        "legacy_ref": LEGACY_REF,
        "current_item_records": len(current),
        "legacy_item_records": len(legacy),
        "common_item_records": len(common_ids),
        "equal_visible_fields": equal_fields,
        "changed_visible_fields": changed_fields,
        "changed_item_records": len(changed_items),
        "changed_fields_with_turkish_chars": changed_with_turkish,
        "legacy_only_visible_fields": legacy_only_fields,
        "current_only_visible_fields": current_only_fields,
        "samples": samples,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    else:
        print("itemInfo legacy recovery audit")
        for key, value in payload.items():
            if key == "samples":
                continue
            print(f"{key}: {value}")
        print("samples:")
        for sample in samples:
            print(json.dumps(sample, ensure_ascii=True, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
