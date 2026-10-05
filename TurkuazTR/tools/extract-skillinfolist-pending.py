#!/usr/bin/env python3
# PATH: /ROenglishRE/TurkuazTR/tools/extract-skillinfolist-pending.py
# PURPOSE: Henuz Turkce SkillName patchi bulunmayan oyuncu skill adlarini raporlar.
# MODULE-FILETYPE: Tool - Python
# VERSION: 1.0.0
# DESCRIPTION: skillinfolist.lub icindeki NV_BASIC sonrasi SkillName kayitlarini SKID bazli patchlerle karsilastirir.
# DEPENDENCY-LAYER: Tool

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INFO_SOURCE = REPO_ROOT / "Translation/Renewal/data/luafiles514/lua files/skillinfoz/skillinfolist.lub"
NAME_PATCH = REPO_ROOT / "TurkuazTR/skillinfolist.tr.json"
OUTPUT = REPO_ROOT / "TurkuazTR/skillinfolist.pending.json"

INFO_ENTRY_RE = re.compile(
    r'\[SKID\.([A-Z0-9_]+)\]\s*=\s*\{.*?SkillName\s*=\s*"([^"]*)"',
    re.S,
)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    info_text = INFO_SOURCE.read_text(encoding="utf-8")
    name_patch = load_json(NAME_PATCH)
    patched = set(name_patch.get("patches", {}))

    entries = [(m.group(1), m.group(2)) for m in INFO_ENTRY_RE.finditer(info_text)]
    start_index = next((i for i, row in enumerate(entries) if row[0] == "NV_BASIC"), -1)
    if start_index < 0:
        raise RuntimeError("NV_BASIC oyuncu skill siniri bulunamadi")

    player_entries = entries[start_index:]
    candidates = [
        {"key": key, "name": name, "order": order}
        for order, (key, name) in enumerate(player_entries, start=1)
        if key not in patched
    ]

    report = {
        "_file_header": {
            "path": "/ROenglishRE/TurkuazTR/skillinfolist.pending.json",
            "purpose": "Henuz Turkce SkillName patchi bulunmayan oyuncu skill adaylarini listeler",
            "module": "Generated Report - JSON",
            "version": "1.0.0",
            "description": (
                "SKILL_INFO_LIST icinde NV_BASIC sinirindan sonraki SkillName "
                f"kayitlarindan uretilir; {len(patched)} oyuncu skill adi patchlendi"
            ),
            "dependency_layer": "Tool",
        },
        "source_path": str(INFO_SOURCE.relative_to(REPO_ROOT)).replace("\\", "/"),
        "patched_count": len(patched),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }

    OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
