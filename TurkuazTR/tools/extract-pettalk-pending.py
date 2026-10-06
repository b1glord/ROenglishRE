#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/extract-pettalk-pending.py
# 📌 Amac: pettalktable.xml icindeki temiz ASCII Ingilizce metinleri raw-byte guvenli pending envanterine donusturur
# 📌 Tool - Python
# Version: 1.1.1
# Aciklama: Kaynagi decode etmeden XML metin dugumlerini siniflandirir; yalniz ASCII ceviri adaylarini metin olarak saklar
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
TAG_RE = re.compile(rb"<([A-Za-z0-9_]+)>([^<]*)</\\1>")
ASCII_LETTER_RE = re.compile(rb"[A-Za-z]")


def git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def main() -> int:
    raw = SOURCE.read_bytes()
    lines = raw.splitlines()

    readable: OrderedDict[bytes, dict] = OrderedDict()
    mixed_unique: set[bytes] = set()
    non_ascii_unique: set[bytes] = set()
    neutral_unique: set[bytes] = set()

    text_node_count = 0
    readable_nodes = 0
    mixed_nodes = 0
    non_ascii_nodes = 0
    neutral_nodes = 0

    for line_no, line in enumerate(lines, start=1):
        for match in TAG_RE.finditer(line):
            value = match.group(2).strip()
            if not value:
                continue

            text_node_count += 1
            ascii_letters = len(ASCII_LETTER_RE.findall(value))
            has_non_ascii = any(byte >= 0x80 for byte in value)

            if ascii_letters >= 3 and not has_non_ascii:
                readable_nodes += 1
                row = readable.setdefault(
                    value,
                    {
                        "text": value.decode("ascii"),
                        "first_line": line_no,
                        "count": 0,
                        "tags": set(),
                    },
                )
                row["count"] += 1
                row["tags"].add(match.group(1).decode("ascii"))
            elif ascii_letters >= 3 and has_non_ascii:
                mixed_nodes += 1
                mixed_unique.add(value)
            elif has_non_ascii:
                non_ascii_nodes += 1
                non_ascii_unique.add(value)
            else:
                neutral_nodes += 1
                neutral_unique.add(value)

    payload = {
        "_file_header": {
            "path": "/ROenglishRE/TurkuazTR/pettalktable.pending.json",
            "purpose": "Pet konusma tablosundaki temiz ASCII Ingilizce ceviri adaylarini raw-byte guvenli bicimde envanterler",
            "module": "Translation Pending - JSON",
            "version": "1.1.0",
            "description": "Kaynak XML'i karakter setine zorlamadan siniflandirir; yalnizca tamamen ASCII olan Ingilizce metinleri pending listesine yazar, mixed/non-ASCII gruplari sayisal kalite ozeti olarak tutar",
            "dependency_layer": "Tool",
        },
        "source_path": "Translation/Renewal/data/pettalktable.xml",
        "source_ref": "upstream/latest",
        "source_blob_sha": git_blob_sha(raw),
        "source_line_count": len(lines),
        "text_node_count": text_node_count,
        "readable_ascii_nodes": readable_nodes,
        "readable_ascii_unique": len(readable),
        "mixed_encoding_nodes": mixed_nodes,
        "mixed_encoding_unique": len(mixed_unique),
        "non_ascii_nodes": non_ascii_nodes,
        "non_ascii_unique": len(non_ascii_unique),
        "neutral_nodes": neutral_nodes,
        "neutral_unique": len(neutral_unique),
        "policy": {
            "readable_ascii": "Turkce ceviri adayi; metin envanterde tutulur",
            "mixed_encoding": "Kaynak/encoding dogrulamasi gerekir; metin envantere kopyalanmaz",
            "non_ascii": "Kaynak dil/encoding tespiti gerekir; metin envantere kopyalanmaz",
            "neutral": "Ceviri gerektirmeyen veya manuel karar gerektiren kisa ifade; metin envantere kopyalanmaz",
        },
        "groups": {
            "readable_ascii": [
                {
                    "text": row["text"],
                    "first_line": row["first_line"],
                    "count": row["count"],
                    "tags": sorted(row["tags"]),
                }
                for row in readable.values()
            ]
        },
    }

    OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
