#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/extract-iteminfo-lore-pending.py
# 📌 Amac: itemInfo Turkce profilinde degismeden kalan gercek lore/aciklama cumlelerini canonical teknik metinlerden ayirip pending raporu uretir
# 📌 Tool - Python
# Version: 1.3.0
# Aciklama: Tum pending metinlerini config kontrollu deterministik sayfalara ayirir
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
BATCH_OUTPUT = REPO_ROOT / "TurkuazTR/iteminfo-lore.batch.json"
BATCH_CONFIG_PATH = REPO_ROOT / "TurkuazTR/config/iteminfo-inventory.json"
RECOVERY = REPO_ROOT / "TurkuazTR/iteminfo-lore.source-recovery.json"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("turkuaz_iteminfo_audit", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("itemInfo audit modulu yuklenemedi")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    batch_config = json.loads(BATCH_CONFIG_PATH.read_text(encoding="utf-8"))
    batch_limit = int(batch_config["batch_limit"])
    if batch_limit <= 0:
        raise ValueError("Batch limit must be positive")
    page_pattern = batch_config["page_pattern"]
    if "{index}" not in page_pattern or "/" in page_pattern or "\\" in page_pattern:
        raise ValueError("Invalid pending inventory page pattern")
    audit = load_audit_module()
    source_data = audit.collect(SOURCE)
    generated_data = audit.collect(GENERATED)

    unchanged = (
        source_data["natural_description"]
        & generated_data["natural_description"]
    )
    recovery_payload = json.loads(RECOVERY.read_text(encoding="utf-8"))
    recovery_texts = set(recovery_payload.get("candidates", []))
    recovery_occurrences = sum(
        count for text, count in unchanged.items() if text in recovery_texts
    )
    rows = [
        {"text": text, "count": count}
        for text, count in unchanged.items()
        if (
            audit.lore_candidate(text)
            and text not in recovery_texts
            and not any(0xD800 <= ord(char) <= 0xDFFF for char in text)
        )
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
        "source_recovery_path": str(RECOVERY.relative_to(REPO_ROOT)),
        "source_recovery_candidate_count": len(recovery_texts),
        "source_recovery_occurrences": recovery_occurrences,
        "candidate_count": len(rows),
        "candidate_occurrences": sum(row["count"] for row in rows),
        "candidates": rows,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    batch_rows = rows[:batch_limit]
    total_pages = max(1, (len(rows) + batch_limit - 1) // batch_limit)
    batch_payload = {
        "_file_header": {
            "path": "/ROenglishRE/TurkuazTR/iteminfo-lore.batch.json",
            "purpose": "Final itemInfo cevirisi icin siradaki guvenli lore adaylarini kucuk ve kolay islenebilir bir batch halinde listeler",
            "module": "Generated Report - JSON",
            "version": "1.0.0",
            "description": "Pending kuyrugunun frekans sirali ilk 1000 adayini final exact ceviri calismasi icin ayri raporlar",
            "dependency_layer": "Tool",
        },
        "source_path": str(SOURCE.relative_to(REPO_ROOT)),
        "pending_path": str(OUTPUT.relative_to(REPO_ROOT)),
        "batch_limit": batch_limit,
        "batch_index": 0,
        "start_offset": 0,
        "total_batch_pages": total_pages,
        "batch_candidate_count": len(batch_rows),
        "remaining_candidate_count": len(rows),
        "remaining_candidate_occurrences": sum(row["count"] for row in rows),
        "candidates": batch_rows,
    }
    BATCH_OUTPUT.write_text(
        json.dumps(batch_payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    expected_pages = set()
    exported_count = len(batch_rows)
    for page_index in range(1, total_pages):
        start_offset = page_index * batch_limit
        page_rows = rows[start_offset:start_offset + batch_limit]
        page_path = BATCH_OUTPUT.with_name(page_pattern.format(index=page_index))
        page_payload = {
            **batch_payload,
            "_file_header": {
                **batch_payload["_file_header"],
                "path": "/ROenglishRE/TurkuazTR/" + page_path.name,
                "description": "Pending itemInfo adaylarinin deterministik sayfasi",
            },
            "batch_index": page_index,
            "start_offset": start_offset,
            "batch_candidate_count": len(page_rows),
            "candidates": page_rows,
        }
        page_path.write_text(
            json.dumps(page_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        expected_pages.add(page_path)
        exported_count += len(page_rows)

    for stale_page in BATCH_OUTPUT.parent.glob(batch_config["page_glob"]):
        if stale_page not in expected_pages:
            stale_page.unlink()

    if exported_count != len(rows):
        raise AssertionError("Paged inventory does not cover entire pending list")

    print(
        f"itemInfo lore pending: {payload['candidate_count']} unique / "
        f"{payload['candidate_occurrences']} occurrences; "
        f"batch={len(batch_rows)}; pages={total_pages}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
