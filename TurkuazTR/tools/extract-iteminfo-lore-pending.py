#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/extract-iteminfo-lore-pending.py
# 📌 Amac: itemInfo Turkce profilinde degismeden kalan gercek lore/aciklama cumlelerini canonical teknik metinlerden ayirip pending raporu uretir
# 📌 Tool - Python
# Version: 1.0.0
# Aciklama: Baseline itemInfo ile generated full_tr profilini karsilastirir ve yalniz lore_candidate filtresinden gecen degismemis aciklamalari frekans sirali JSON raporuna yazar
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = REPO_ROOT / "TurkuazTR/tools/audit-iteminfo-visible.py"
SOURCE = REPO_ROOT / "Translation/Renewal/SystemEN/LuaFiles514/itemInfo.lua"
GENERATED = REPO_ROOT / "TurkuazTR/generated/full_tr/SystemEN/LuaFiles514/itemInfo.lua"
OUTPUT = REPO_ROOT / "TurkuazTR/iteminfo-lore.pending.json"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("turkuaz_iteminfo_audit", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("itemInfo audit modulu yuklenemedi")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    audit = load_audit_module()
    source_data = audit.collect(SOURCE)
    generated_data = audit.collect(GENERATED)

    unchanged = (
        source_data["natural_description"]
        & generated_data["natural_description"]
    )
    rows = [
        {"text": text, "count": count}
        for text, count in unchanged.items()
        if audit.lore_candidate(text)
    ]
    rows.sort(key=lambda row: (-row["count"], row["text"]))

    payload = {
        "_file_header": {
            "path": "/ROenglishRE/TurkuazTR/iteminfo-lore.pending.json",
            "purpose": "itemInfo icinde hala Turkcelestirilmemis gercek lore ve serbest aciklama adaylarini listeler",
            "module": "Generated Report - JSON",
            "version": "1.0.0",
            "description": "Canonical stat, job, NAVI ve teknik satirlar elendikten sonra baseline ile ayni kalan lore adaylarini frekans sirali raporlar",
            "dependency_layer": "Tool",
        },
        "source_path": str(SOURCE.relative_to(REPO_ROOT)),
        "generated_path": str(GENERATED.relative_to(REPO_ROOT)),
        "candidate_count": len(rows),
        "candidate_occurrences": sum(row["count"] for row in rows),
        "candidates": rows,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"itemInfo lore pending: {payload['candidate_count']} unique / "
        f"{payload['candidate_occurrences']} occurrences"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
