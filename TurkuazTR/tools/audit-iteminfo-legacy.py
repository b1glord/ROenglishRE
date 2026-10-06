#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/audit-iteminfo-legacy.py
# 📌 Amac: Guncel itemInfo.lua ile eski Turkce arsiv dalini item ID ve gorunur alan bazinda karsilastirip geri kazanilabilir ceviri kapsamini olcer
# 📌 Tool - Python
# Version: 1.0.0
# Aciklama: identified/unidentified ad ve aciklama alanlarini iki ref arasinda byte-safe karsilastirir; ayni, farkli ve legacy-only alanlari raporlar
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    current = parse_visible(read_current())
    legacy = parse_visible(read_ref(LEGACY_REF))

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
