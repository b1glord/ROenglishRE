#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/validate-iteminfo-paged-inventory.py
# 📌 Amac: Tum itemInfo pending adaylarinin bolunmeden veya tekrarlanmadan batch sayfalarinda yer aldigini dogrular
# 📌 Modul - Tool Python
# Version: 1.0.0
# Aciklama: Sayfa siniri, tum kayitlar, baslangic indeksi ve eski dosya temizligini denetler
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "TurkuazTR/iteminfo-lore.pending.json"
PRIMARY_BATCH = ROOT / "TurkuazTR/iteminfo-lore.batch.json"
CONFIG = ROOT / "TurkuazTR/config/iteminfo-inventory.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    cfg = read_json(CONFIG)
    limit = int(cfg["batch_limit"])
    if limit <= 0:
        raise ValueError("Invalid itemInfo page size")

    inventory = read_json(INVENTORY)
    rows = inventory["candidates"]
    total_pages = max(1, (len(rows) + limit - 1) // limit)
    expected_pages = set()

    for index in range(total_pages):
        path = (
            PRIMARY_BATCH
            if index == 0
            else PRIMARY_BATCH.with_name(cfg["page_pattern"].format(index=index))
        )
        page = read_json(path)
        start = index * limit
        portion = rows[start:start + limit]
        if page["batch_index"] != index:
            raise AssertionError(f"Wrong page index: {path}")
        if page["start_offset"] != start:
            raise AssertionError(f"Wrong offset: {path}")
        if page["total_batch_pages"] != total_pages:
            raise AssertionError(f"Wrong page count: {path}")
        if page["remaining_candidate_count"] != len(rows):
            raise AssertionError(f"Wrong inventory total: {path}")
        if page["batch_candidate_count"] != len(portion):
            raise AssertionError(f"Wrong page size: {path}")
        if page["candidates"] != portion:
            raise AssertionError(f"Missing, changed or reordered candidates: {path}")
        if index > 0:
            expected_pages.add(path)

    actual_pages = set(PRIMARY_BATCH.parent.glob(cfg["page_glob"]))
    if actual_pages != expected_pages:
        raise AssertionError(
            f"Extra or missing itemInfo inventory pages: "
            f"extra={sorted(str(x) for x in actual_pages - expected_pages)}, "
            f"missing={sorted(str(x) for x in expected_pages - actual_pages)}"
        )

    print(f"itemInfo pending windows PASS: {len(rows)} records, {total_pages} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
