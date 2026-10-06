#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/audit-iteminfo-visible.py
# 📌 Amac: Buyuk itemInfo.lua dosyasindaki oyuncuya gorunen item ad/aciklama alanlarini teknik alanlardan ayirip sayisal kapsam raporu uretir
# 📌 Tool - Python
# Version: 1.0.0
# Aciklama: identified/unidentified display name ve description alanlarini tarar; item kaydi, gorunen string ve teknik field sayilarini raporlar
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "Translation/Renewal/SystemEN/LuaFiles514/itemInfo.lua"

ENTRY_RE = re.compile(r"^\s*\[(\d+)\]\s*=\s*\{")
FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*)$")
STRING_RE = re.compile(r'"((?:\\.|[^"\\])*)"')

VISIBLE_FIELDS = {
    "unidentifiedDisplayName",
    "unidentifiedDescriptionName",
    "identifiedDisplayName",
    "identifiedDescriptionName",
}
NAME_FIELDS = {"unidentifiedDisplayName", "identifiedDisplayName"}
DESCRIPTION_FIELDS = {"unidentifiedDescriptionName", "identifiedDescriptionName"}


def count_strings(value: str) -> int:
    return len(STRING_RE.findall(value))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = SOURCE.read_text(encoding="utf-8", errors="surrogateescape")
    lines = text.splitlines()

    item_count = 0
    field_counts: dict[str, int] = {}
    visible_field_occurrences = 0
    visible_string_count = 0
    name_string_count = 0
    description_string_count = 0
    technical_field_occurrences = 0

    active_visible_field: str | None = None
    brace_depth = 0

    for line in lines:
        if ENTRY_RE.match(line):
            item_count += 1

        match = FIELD_RE.match(line)
        if match:
            field, value = match.groups()
            field_counts[field] = field_counts.get(field, 0) + 1

            if field in VISIBLE_FIELDS:
                visible_field_occurrences += 1
                active_visible_field = field
                strings = count_strings(value)
                visible_string_count += strings
                if field in NAME_FIELDS:
                    name_string_count += strings
                else:
                    description_string_count += strings

                if "{" in value and "}" not in value:
                    brace_depth = value.count("{") - value.count("}")
                else:
                    active_visible_field = None
                    brace_depth = 0
            else:
                technical_field_occurrences += 1
                active_visible_field = None
                brace_depth = 0
            continue

        if active_visible_field is not None:
            strings = count_strings(line)
            visible_string_count += strings
            if active_visible_field in NAME_FIELDS:
                name_string_count += strings
            else:
                description_string_count += strings

            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                active_visible_field = None
                brace_depth = 0

    payload = {
        "source": str(SOURCE.relative_to(REPO_ROOT)),
        "source_lines": len(lines),
        "item_records": item_count,
        "visible_field_occurrences": visible_field_occurrences,
        "visible_string_count": visible_string_count,
        "name_string_count": name_string_count,
        "description_string_count": description_string_count,
        "technical_field_occurrences": technical_field_occurrences,
        "field_counts": dict(sorted(field_counts.items())),
        "visible_fields": sorted(VISIBLE_FIELDS),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    else:
        print("itemInfo visible audit")
        for key, value in payload.items():
            if key == "field_counts":
                continue
            print(f"{key}: {value}")
        print("field_counts:")
        for key, value in payload["field_counts"].items():
            print(f"  {key}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
