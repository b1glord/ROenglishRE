#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/audit-iteminfo-visible.py
# 📌 Amac: Buyuk itemInfo.lua dosyasindaki oyuncuya gorunen item ad/aciklama alanlarini teknik alanlardan ayirip ceviri kapsamini ve tekrar frekanslarini raporlar
# 📌 Tool - Python
# Version: 1.10.0
# Aciklama: Kaynak veya generated itemInfo profilini tarar; base-stat, Grade/stat, loot-oran, miktarli item satirlari ve canonical title/job listelerini teknik metin olarak eleyip lore adaylarini guvenli bicimde raporlar
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


def strings(value: str) -> list[str]:
    return STRING_RE.findall(value)


def natural_candidate(value: str) -> bool:
    clean = COLOR_RE.sub("", value)
    if clean.strip("_ -\t\r\n") == "":
        return False
    return len(LETTER_RE.findall(clean)) >= 4


STAT_ONLY_RE = re.compile(
    r"^(?:(?:Max(?:HP|SP)|HP|SP|ATK|MATK|MDEF|DEF|HIT|FLEE|ASPD|Critical|Perfect Dodge|"
    r"P\.ATK|S\.MATK|STR|AGI|VIT|INT|DEX|LUK|POW|STA|WIS|SPL|CON|CRT)(?:\s*[+\-]?[0-9.%]+)?"
    r"(?:,?\s*)?)+\.?$",
    re.IGNORECASE,
)
GRADE_STAT_RE = re.compile(r"^\[Grade [A-D]\]:\s*[A-Z.]+\s*[+\-]?[0-9.%]+\.?$")
STAT_ASSIGN_RE = re.compile(
    r"^(?:Max(?:HP|SP)|HP|SP|ATK|MATK|MDEF|DEF|HIT|FLEE|ASPD|Critical|Perfect Dodge|"
    r"P\.ATK|S\.MATK|STR|AGI|VIT|INT|DEX|LUK|POW|STA|WIS|SPL|CON|CRT)\s*[+\-]?[0-9.]+%?$",
    re.IGNORECASE,
)
SHORT_CANONICAL_RE = re.compile(r"^[A-Z][A-Za-z0-9'().-]*(?:[ ,/-]+[A-Z][A-Za-z0-9'().-]*){0,3}$")
LOOT_RATE_RE = re.compile(r"^.+?\s+x\d+\s+\d+(?:\.\d+)?%,?$")
CANONICAL_TITLE_RE = re.compile(r"^(?:Crown of Good and Evil\(.+\)|VR Book: .+)$")
QUANTITY_ITEM_RE = re.compile(r"^\d+x\s+.+$")
COSTUME_TITLE_RE = re.compile(r"^Costume:\s+.+$")
PAREN_CANONICAL_LIST_RE = re.compile(r"^\([A-Za-z0-9' -]+(?:,\s*[A-Za-z0-9' -]+){2,}\)$")
JOB_LIST_RE = re.compile(
    r"^(?=.*(?:Swordsman|Magician|Archer|Merchant|Thief|Acolyte|Novice|Rune Knight|Royal Guard|Mechanic|Genetic|Archbishop|Sura|Soul Linker|Ninja))"
    r"[A-Za-z0-9 ,;/&()'\-]+(?:classes?)?$"
)


def grade_stat_only(value: str) -> bool:
    match = re.fullmatch(r"\[Grade [A-D]\]:\s*(.+?)\.?", value)
    if not match:
        return False
    body = match.group(1).rstrip(".")
    parts = [part.strip() for part in body.split(",") if part.strip()]
    return bool(parts) and all(STAT_ASSIGN_RE.fullmatch(part) for part in parts)


def canonical_name_list(value: str) -> bool:
    """Exclude pure proper-name item and location lists, not real descriptions."""
    parts = [part.strip(" -.\t") for part in value.split(",")]
    if len(parts) < 3 or re.search(
        r"\b(?:etc|chance|randomly|obtain|can|will|added|contains|including|"
        r"available|increases|decreases|among|have been)\b",
        value,
        re.IGNORECASE,
    ):
        return False
    connectors = {"of", "the", "and", "in", "to", "for", "under", "on", "with", "de", "a", "or"}
    for part in parts:
        without_counts = re.sub(r"\([^)]*\)|\[[^]]*\]|\b\d+(?:\.\d+)?\b", "", part)
        words = re.findall(r"[A-Za-z]+", without_counts)
        if not words or not all(
            word[0].isupper() or word.lower() in connectors for word in words
        ):
            return False
    return True


def lore_candidate(value: str) -> bool:
    clean = COLOR_RE.sub("", value).strip()
    if not natural_candidate(clean):
        return False
    if clean.startswith("<NAVI>") or "<INFO>" in clean:
        return False
    if canonical_name_list(clean):
        return False
    if LOOT_RATE_RE.fullmatch(clean):
        return False
    if (
        CANONICAL_TITLE_RE.fullmatch(clean)
        or QUANTITY_ITEM_RE.fullmatch(clean)
        or COSTUME_TITLE_RE.fullmatch(clean)
        or PAREN_CANONICAL_LIST_RE.fullmatch(clean)
        or JOB_LIST_RE.fullmatch(clean)
        or (clean.endswith(" Equipment") and "," in clean and len(clean.split(",")) >= 6)
    ):
        return False
    if (
        STAT_ONLY_RE.fullmatch(clean)
        or GRADE_STAT_RE.fullmatch(clean)
        or grade_stat_only(clean)
    ):
        return False
    if SHORT_CANONICAL_RE.fullmatch(clean) and len(clean.split()) <= 4:
        return False
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", clean)
    if len(words) < 5:
        return False
    return (
        any(mark in clean for mark in (".", "!", "?", ":"))
        or len(words) >= 8
    )


def resolve_source(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def display_source(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def collect(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
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

    return {
        "source_lines": len(lines),
        "item_records": item_count,
        "visible_field_occurrences": visible_field_occurrences,
        "technical_field_occurrences": technical_field_occurrences,
        "field_counts": dict(sorted(field_counts.items())),
        "name_counter": name_counter,
        "description_counter": description_counter,
        "all_counter": all_counter,
        "natural_description": natural_description,
    }


def top_rows(counter: Counter[str], limit: int) -> list[dict[str, object]]:
    return [
        {"text": text, "count": count}
        for text, count in counter.most_common(limit)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--source", default=str(SOURCE.relative_to(REPO_ROOT)))
    parser.add_argument("--baseline-source")
    parser.add_argument("--top", type=int, default=60)
    args = parser.parse_args()

    source_path = resolve_source(args.source)
    data = collect(source_path)

    name_counter = data["name_counter"]
    description_counter = data["description_counter"]
    all_counter = data["all_counter"]
    natural_description = data["natural_description"]

    payload = {
        "source": display_source(source_path),
        "source_lines": data["source_lines"],
        "item_records": data["item_records"],
        "visible_field_occurrences": data["visible_field_occurrences"],
        "visible_string_count": sum(all_counter.values()),
        "unique_visible_string_count": len(all_counter),
        "name_string_count": sum(name_counter.values()),
        "unique_name_string_count": len(name_counter),
        "description_string_count": sum(description_counter.values()),
        "unique_description_string_count": len(description_counter),
        "natural_description_occurrences": sum(natural_description.values()),
        "unique_natural_description_count": len(natural_description),
        "technical_field_occurrences": data["technical_field_occurrences"],
        "field_counts": data["field_counts"],
        "visible_fields": sorted(VISIBLE_FIELDS),
        "top_natural_description_strings": top_rows(natural_description, args.top),
    }

    if args.baseline_source:
        baseline_path = resolve_source(args.baseline_source)
        baseline = collect(baseline_path)
        baseline_natural = baseline["natural_description"]
        unchanged_natural = natural_description & baseline_natural
        unchanged_lore = Counter(
            {
                key: value
                for key, value in unchanged_natural.items()
                if lore_candidate(key)
            }
        )
        payload.update(
            {
                "baseline_source": display_source(baseline_path),
                "unchanged_natural_description_occurrences": sum(
                    unchanged_natural.values()
                ),
                "unique_unchanged_natural_description_count": len(unchanged_natural),
                "unchanged_lore_candidate_occurrences": sum(
                    unchanged_lore.values()
                ),
                "unique_unchanged_lore_candidate_count": len(unchanged_lore),
                "top_unchanged_natural_description_strings": top_rows(
                    unchanged_natural, args.top
                ),
                "top_unchanged_lore_candidates": top_rows(
                    unchanged_lore, args.top
                ),
            }
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    else:
        print("itemInfo visible audit")
        for key, value in payload.items():
            if key in {
                "field_counts",
                "top_natural_description_strings",
                "top_unchanged_natural_description_strings",
                "top_unchanged_lore_candidates",
            }:
                continue
            print(f"{key}: {value}")
        print("top_natural_description_strings:")
        for row in payload["top_natural_description_strings"]:
            print(json.dumps(row, ensure_ascii=True, sort_keys=True))
        if "top_unchanged_natural_description_strings" in payload:
            print("top_unchanged_natural_description_strings:")
            for row in payload["top_unchanged_natural_description_strings"]:
                print(json.dumps(row, ensure_ascii=True, sort_keys=True))
        if "top_unchanged_lore_candidates" in payload:
            print("top_unchanged_lore_candidates:")
            for row in payload["top_unchanged_lore_candidates"]:
                print(json.dumps(row, ensure_ascii=True, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
