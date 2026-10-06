#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/build-iteminfo-profile.py
# 📌 Amac: itemInfo.lua dosyasinin gorunur aciklama bloklarina config tabanli byte-safe Turkce metadata kurallarini uygular
# 📌 Tool - Python
# Version: 1.1.1
# Aciklama: Exact serbest aciklama overlay'i icin string matcher tanimini tamamlar; byte-safe sistem kurallariyla birlikte description alanlarinda uygular
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = REPO_ROOT / "TurkuazTR/localization-profiles.json"
CONFIG_PATH = REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json"

FIELD_RE = re.compile(rb"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*)$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_rules(rules: list[dict]) -> list[dict]:
    prepared: list[dict] = []
    for rule in rules:
        rule_id = rule["id"]
        rule_type = rule["type"]

        if rule_type == "literal":
            prepared.append(
                {
                    "id": rule_id,
                    "type": rule_type,
                    "source": rule["source"].encode("ascii"),
                    "target": rule["translation"].encode("ascii"),
                }
            )
        elif rule_type == "regex":
            prepared.append(
                {
                    "id": rule_id,
                    "type": rule_type,
                    "pattern": re.compile(rule["pattern"].encode("ascii")),
                    "replacement": rule["replacement"].encode("ascii"),
                }
            )
        else:
            raise ValueError(f"Unsupported rule type: {rule_type}")

    return prepared


def prepare_exact_translations(data: dict) -> dict[bytes, bytes]:
    prepared: dict[bytes, bytes] = {}
    for source, translation in data.get("translations", {}).items():
        source_bytes = source.encode("ascii")
        target_bytes = translation.encode("ascii")
        if not source_bytes:
            raise ValueError("Empty item info exact translation source")
        if source_bytes == target_bytes:
            raise ValueError(f"Exact translation does not change source: {source!r}")
        prepared[source_bytes] = target_bytes
    return prepared


def apply_exact_translations(
    line: bytes,
    translations: dict[bytes, bytes],
    counts: dict[str, int],
) -> bytes:
    if not translations:
        return line

    def replace(match: re.Match[bytes]) -> bytes:
        source = match.group(1)
        target = translations.get(source)
        if target is None:
            return match.group(0)
        counts["exact_translation"] = counts.get("exact_translation", 0) + 1
        return b'"' + target + b'"'

    return STRING_RE.sub(replace, line)


def apply_rules(line: bytes, rules: list[dict], counts: dict[str, int]) -> bytes:
    result = line
    for rule in rules:
        rule_id = rule["id"]
        if rule["type"] == "literal":
            source = rule["source"]
            target = rule["target"]
            count = result.count(source)
            if count:
                result = result.replace(source, target)
                counts[rule_id] = counts.get(rule_id, 0) + count
        else:
            result, count = rule["pattern"].subn(rule["replacement"], result)
            if count:
                counts[rule_id] = counts.get(rule_id, 0) + count
    return result


def build(profile: str) -> tuple[bytes, dict[str, object]]:
    profiles = load_json(PROFILE_PATH)
    config = load_json(CONFIG_PATH)

    profile_data = profiles["profiles"][profile]
    mode = profile_data["item_info"]
    source = REPO_ROOT / config["source_path"]
    raw = source.read_bytes()

    if mode == "original":
        return raw, {
            "profile": profile,
            "mode": mode,
            "total_replacements": 0,
            "rule_counts": {},
            "input_bytes": len(raw),
            "output_bytes": len(raw),
        }

    if mode != "tr_metadata":
        raise ValueError(f"Unsupported item_info mode: {mode}")

    target_fields = {field.encode("ascii") for field in config["target_fields"]}
    exact_path = REPO_ROOT / config["exact_translation_path"]
    exact_translations = prepare_exact_translations(load_json(exact_path))
    rules = prepare_rules(config["rules"])
    counts: dict[str, int] = {}

    output: list[bytes] = []
    active_description = False
    brace_depth = 0

    for line in raw.splitlines(keepends=True):
        field_match = FIELD_RE.match(line)
        if field_match:
            field, value = field_match.groups()
            active_description = field in target_fields
            if active_description:
                line = apply_exact_translations(line, exact_translations, counts)
                line = apply_rules(line, rules, counts)
                brace_depth = value.count(b"{") - value.count(b"}")
                if brace_depth <= 0:
                    active_description = False
                    brace_depth = 0
            else:
                brace_depth = 0
            output.append(line)
            continue

        if active_description:
            line = apply_exact_translations(line, exact_translations, counts)
            line = apply_rules(line, rules, counts)
            brace_depth += line.count(b"{") - line.count(b"}")
            if brace_depth <= 0:
                active_description = False
                brace_depth = 0

        output.append(line)

    built = b"".join(output)
    summary = {
        "profile": profile,
        "mode": mode,
        "total_replacements": sum(counts.values()),
        "exact_translation_count": counts.get("exact_translation", 0),
        "applied_rule_count": len([key for key in counts if key != "exact_translation"]),
        "rule_counts": dict(sorted((key, value) for key, value in counts.items() if key != "exact_translation")),
        "input_bytes": len(raw),
        "output_bytes": len(built),
    }
    return built, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    profiles = load_json(PROFILE_PATH)["profiles"]
    if args.profile not in profiles:
        raise SystemExit(f"Unknown profile: {args.profile}")

    built, summary = build(args.profile)

    if args.check:
        if summary["mode"] == "tr_metadata" and summary["total_replacements"] <= 0:
            raise SystemExit("No item info translation rules matched")
        print(json.dumps(summary, ensure_ascii=True, sort_keys=True))
        return 0

    if not args.output:
        raise SystemExit("--output is required unless --check is used")

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(built)
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
