#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/audit-iteminfo-visible.py
# 📌 Amac: Buyuk itemInfo.lua dosyasindaki oyuncuya gorunen item ad/aciklama alanlarini teknik alanlardan ayirip ceviri kapsamini ve tekrar frekanslarini raporlar
# 📌 Tool - Python
# Version: 1.1.0
# Aciklama: identified/unidentified display name ve description alanlarini tarar; occurrence, unique string ve en sik dogal dil adaylarini raporlar
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "Translation/Renewal/SystemEN/LuaFiles514/itemInfo.lua"

ENTRY_RE = re.compile(r"^\s*\[(\d+)\]\s*=\s*\{")
FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*)$")
STRING_RE = re.compile(r'"((?:\\.|[^"\\])*)"')
COLOR_RE = re.compile(r"\^[0-9A-Fa-f]{6}")
LETTER_RE = re.compile(r"[A-Za-z]")

VISIBLE_FIELDS = {
    "unidentifiedDisplayName",
    "unidentifiedDescriptionName",
    "identifiedDisplayName",
    "identifiedDescriptionName",
}
NAME_FIELDS = {"unidentifiedDisplayName", "identifiedDisplayName"}
DESCRIPTION_FIELDS = {"unidentifiedDescriptionName", "identifiedDescriptionName"}


def strings(value: str) -> list[str]:
    return STRING_RE.findall(value)


def natural_candidate(value: str) -> bool:
    clean = COLOR_RE.sub("", value)
    if clean.strip("_ -\t\r\n") == "":
        return False
    return len(LETTER_RE.findall(clean)) >= 4


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = SOURCE.read_text(encoding="utf-8", errors="surrogateescape")
    lines = text.splitlines()

    item_count = 0
    field_counts: dict[str, int] = {}
    visible_field_occurrences = 0
    technical_field_occurrences = 0

    name_counter: Counter[str] = Counter()
    description_counter: Counter[str] = Counter()

    active_visible_field: str | None = None
    brace_depth = 0

    def add_values(field: str, values: list[str]) -> None:
        counter = name_counter if field in NAME_FIELDS else description_counter
        for value in values:
            if value:
                counter[value] += 1

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
                add_values(field, strings(value))

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
            add_values(active_visible_field, strings(line))
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                active_visible_field = None
                brace_depth = 0

    all_counter = name_counter + description_counter
    natural_description = Counter(
        {key: value for key, value in description_counter.items() if natural_candidate(key)}
    )

    payload = {
        "source": str(SOURCE.relative_to(REPO_ROOT)),
        "source_lines": len(lines),
        "item_records": item_count,
        "visible_field_occurrences": visible_field_occurrences,
        "visible_string_count": sum(all_counter.values()),
        "unique_visible_string_count": len(all_counter),
        "name_string_count": sum(name_counter.values()),
        "unique_name_string_count": len(name_counter),
        "description_string_count": sum(description_counter.values()),
        "unique_description_string_count": len(description_counter),
        "natural_description_occurrences": sum(natural_description.values()),
        "unique_natural_description_count": len(natural_description),
        "technical_field_occurrences": technical_field_occurrences,
        "field_counts": dict(sorted(field_counts.items())),
        "visible_fields": sorted(VISIBLE_FIELDS),
        "top_natural_description_strings": [
            {"text": text, "count": count}
            for text, count in natural_description.most_common(60)
        ],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    else:
        print("itemInfo visible audit")
        for key, value in payload.items():
            if key in {"field_counts", "top_natural_description_strings"}:
                continue
            print(f"{key}: {value}")
        print("top_natural_description_strings:")
        for row in payload["top_natural_description_strings"]:
            print(json.dumps(row, ensure_ascii=True, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
