#!/usr/bin/env python3
# PATH: /ROenglishRE/TurkuazTR/tools/extract-skilldescript-pending.py
# PURPOSE: Renewal skill aciklamalarindan Turkce ceviri bekleyen adaylari UTF-8 JSON raporuna cikarir.
# MODULE-FILETYPE: Tool - Python
# VERSION: 1.0.0
# DESCRIPTION: CP949/EUC-KR/UTF-8 skilldescript kaynagini okur, SKID bazli pending raporu uretir.
# DEPENDENCY-LAYER: Tool

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INFO_SOURCE = REPO_ROOT / "Translation/Renewal/data/luafiles514/lua files/skillinfoz/skillinfolist.lub"
DESC_SOURCE = REPO_ROOT / "Translation/Renewal/data/luafiles514/lua files/skillinfoz/skilldescript.lub"
NAME_PATCH = REPO_ROOT / "TurkuazTR/skillinfolist.tr.json"
DESC_PATCH = REPO_ROOT / "TurkuazTR/skilldescript.tr.json"
OUTPUT = REPO_ROOT / "TurkuazTR/skilldescript.pending.json"

BLOCK_START_RE = re.compile(r"\\[SKID\\.([A-Z0-9_]+)\\]\\s*=\\s*\\{")
INFO_ENTRY_RE = re.compile(
    r"\\[SKID\\.([A-Z0-9_]+)\\]\\s*=\\s*\\{.*?SkillName\\s*=\\s*\\\"([^\\\"]*)\\\"",
    re.S,
)
LUA_STRING_RE = re.compile(r'\\"(?:\\\\.|[^\\"\\\\])*\\"')


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_source(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ("cp949", "euc-kr", "utf-8"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Desteklenmeyen encoding: {path}")


def parse_lua_string(token: str) -> str:
    try:
        return ast.literal_eval(token)
    except (SyntaxError, ValueError):
        body = token[1:-1]
        return body.replace(r'\\\"', '"').replace(r"\\\\", "\\")


def extract_blocks(text: str) -> dict[str, dict]:
    starts = list(BLOCK_START_RE.finditer(text))
    result: dict[str, dict] = {}
    for index, match in enumerate(starts):
        start = match.start()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[start:end]
        strings = [parse_lua_string(x.group(0)) for x in LUA_STRING_RE.finditer(block)]
        result[match.group(1)] = {
            "line": text.count("\\n", 0, start) + 1,
            "strings": strings,
        }
    return result


def main() -> int:
    info_text = INFO_SOURCE.read_text(encoding="utf-8")
    desc_text, desc_encoding = read_source(DESC_SOURCE)

    name_patch = load_json(NAME_PATCH)
    desc_patch = load_json(DESC_PATCH)
    patched = set(desc_patch.get("patches", {}))

    entries = [(m.group(1), m.group(2)) for m in INFO_ENTRY_RE.finditer(info_text)]
    start_index = next((i for i, row in enumerate(entries) if row[0] == "NV_BASIC"), -1)
    if start_index < 0:
        raise RuntimeError("NV_BASIC oyuncu skill siniri bulunamadi")

    player_entries = entries[start_index:]
    blocks = extract_blocks(desc_text)
    name_rows = name_patch.get("patches", {})

    candidates = []
    missing = []
    for order, (key, current_name) in enumerate(player_entries, start=1):
        if key in patched:
            continue

        block = blocks.get(key)
        if not block:
            missing.append({"key": key, "name": current_name, "order": order})
            continue

        strings = block["strings"]
        original_name = name_rows.get(key, {}).get("name_original") or (strings[0] if strings else current_name)
        lines_en = strings[1:] if len(strings) > 1 else []

        candidates.append(
            {
                "key": key,
                "order": order,
                "line": block["line"],
                "name_original": original_name,
                "lines_en": lines_en,
            }
        )

    report = {
        "_file_header": {
            "path": "/ROenglishRE/TurkuazTR/skilldescript.pending.json",
            "purpose": "Henuz Turkce description patchi bulunmayan Renewal oyuncu skill adaylarini listeler",
            "module": "Generated Report - JSON",
            "version": "1.0.0",
            "description": "CP949/EUC-KR fallback ile skilldescript.lub kaynagindan SKID bazli uretilir",
            "dependency_layer": "Tool",
        },
        "source_path": str(DESC_SOURCE.relative_to(REPO_ROOT)).replace("\\\\", "/"),
        "source_encoding": desc_encoding,
        "patched_count": len(patched),
        "candidate_count": len(candidates),
        "missing_description_count": len(missing),
        "candidates": candidates,
        "missing_descriptions": missing,
    }

    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
