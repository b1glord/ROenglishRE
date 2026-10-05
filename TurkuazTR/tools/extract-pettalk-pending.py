#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/extract-pettalk-pending.py
# 📌 Amac: pettalktable.xml icindeki metin dugumlerini encoding kalitesine gore siniflandirip pending ceviri envanteri uretir
# 📌 Tool - Python
# Version: 1.0.0
# Aciklama: Okunabilir ASCII Ingilizce, karisik encoding, non-ASCII ve neutral pet konusmalarini ayri raporlar
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "Translation/Renewal/data/pettalktable.xml"
OUTPUT = REPO_ROOT / "TurkuazTR/pettalktable.pending.json"
TAG_RE = re.compile(r"<([A-Za-z0-9_]+)>([^<]*)</\\1>")


def classify(value: str) -> str:
    ascii_letters = len(re.findall(r"[A-Za-z]", value))
    non_ascii = sum(1 for char in value if ord(char) > 127)
    if ascii_letters >= 3 and non_ascii == 0:
        return "readable_ascii"
    if ascii_letters >= 3 and non_ascii > 0:
        return "mixed_encoding"
    if non_ascii > 0:
        return "non_ascii"
    return "neutral"


def main() -> int:
    raw = SOURCE.read_bytes()
    text = raw.decode("utf-8")
    lines = text.splitlines()
    blob_header = f"blob {len(raw)}\\0".encode("ascii")
    source_blob_sha = hashlib.sha1(blob_header + raw).hexdigest()
    groups: dict[str, OrderedDict[str, dict]] = {
        "readable_ascii": OrderedDict(),
        "mixed_encoding": OrderedDict(),
        "non_ascii": OrderedDict(),
        "neutral": OrderedDict(),
    }
    node_count = 0

    for line_no, line in enumerate(lines, start=1):
        for match in TAG_RE.finditer(line):
            value = match.group(2).strip()
            if not value:
                continue
            node_count += 1
            bucket = classify(value)
            row = groups[bucket].setdefault(
                value,
                {"text": value, "first_line": line_no, "count": 0, "tags": set()},
            )
            row["count"] += 1
            row["tags"].add(match.group(1))

    rendered_groups = {}
    summary = {}
    for bucket, rows in groups.items():
        rendered = []
        node_total = 0
        for row in rows.values():
            node_total += row["count"]
            rendered.append(
                {
                    "text": row["text"],
                    "first_line": row["first_line"],
                    "count": row["count"],
                    "tags": sorted(row["tags"]),
                }
            )
        rendered_groups[bucket] = rendered
        summary[f"{bucket}_nodes"] = node_total
        summary[f"{bucket}_unique"] = len(rendered)

    payload = {
        "_file_header": {
            "path": "/ROenglishRE/TurkuazTR/pettalktable.pending.json",
            "purpose": "Pet konusma tablosundaki ceviri adaylarini encoding kalitesine gore ayirir ve kontrollu Turkce ceviri dilimleri icin kaynak envanteri saglar",
            "module": "Translation Pending - JSON",
            "version": "1.0.0",
            "description": "Okunabilir ASCII Ingilizce, karisik encoding, non-ASCII ve neutral pet konusmalarini ayri gruplar; bozuk kaynagi otomatik ceviri olarak sabitlemez",
            "dependency_layer": "Tool",
        },
        "source_path": "Translation/Renewal/data/pettalktable.xml",
        "source_ref": "upstream/latest",
        "source_blob_sha": source_blob_sha,
        "source_line_count": len(lines),
        "text_node_count": node_count,
        **summary,
        "policy": {
            "readable_ascii": "Turkce ceviri adayi",
            "mixed_encoding": "Once kaynak/encoding duzeltmesi veya upstream karsilastirmasi gerekir",
            "non_ascii": "Once kaynak dil ve encoding tespiti gerekir",
            "neutral": "Ceviri gerektirmeyen veya manuel karar gerektiren kisa ifade",
        },
        "groups": rendered_groups,
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
