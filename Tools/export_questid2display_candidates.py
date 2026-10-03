#!/usr/bin/env python3
# Dosya Yolu: /ROenglishRE/Tools/export_questid2display_candidates.py
# Amac: Legacy questid2display.txt icinden ceviri patchinde olmayan quest adaylarini UTF-8 JSON rapora cikarir
# Modul: Tool - Python
# Version: 1.0.0
# Aciklama: Kaynak dosyayi byte olarak okur, CP949 ile decode eder ve patchlenmemis quest kayitlarini raporlar
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

HEADER_RE = re.compile(rb"^(\d+)#([^#]*)#([^#]*)#([^#]*)#$")


def git_show(repo_root: Path, ref_name: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref_name}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout


def decode_field(value: bytes) -> str:
    for encoding in ("cp949", "euc-kr"):
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            pass
    return value.decode("latin-1")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--path",
        default="Translation/Renewal/data/questid2display.txt",
    )
    parser.add_argument(
        "--patch",
        default="TurkuazTR/questid2display.tr.json",
    )
    parser.add_argument(
        "--source-ref",
        default="refs/remotes/origin/upstream/latest",
    )
    parser.add_argument(
        "--output",
        default="TurkuazTR/questid2display.pending.json",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else script_path.parent.parent
    )

    patch_cfg = json.loads(
        (repo_root / args.patch).read_text(encoding="utf-8")
    )
    patched = set(patch_cfg["patches"])

    source = git_show(repo_root, args.source_ref, args.path)
    lines = source.replace(b"\r\n", b"\n").split(b"\n")

    candidates: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        match = HEADER_RE.match(line)
        if not match or index + 2 >= len(lines):
            continue

        quest_id = match.group(1).decode("ascii")
        if quest_id in patched:
            continue

        title = decode_field(match.group(2))
        description = decode_field(lines[index + 1][:-1] if lines[index + 1].endswith(b"#") else lines[index + 1])
        goal = decode_field(lines[index + 2][:-1] if lines[index + 2].endswith(b"#") else lines[index + 2])

        searchable = f"{title} {description} {goal}"
        if not re.search(r"[A-Za-z]{4,}", searchable):
            continue

        candidates.append(
            {
                "id": quest_id,
                "line": index + 1,
                "title": title,
                "description": description,
                "goal": goal,
            }
        )

    output = {
        "_file_header": {
            "path": "/ROenglishRE/TurkuazTR/questid2display.pending.json",
            "purpose": "Quest ceviri patchinde henuz bulunmayan upstream quest adaylarini listeler",
            "module": "Generated Report - JSON",
            "version": "1.0.0",
            "description": "Raw questid2display byte kaynagindan CP949/EUC-KR fallback ile uretilir",
            "dependency_layer": "Tool",
        },
        "source_ref": args.source_ref,
        "patched_count": len(patched),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }

    target = repo_root / args.output
    target.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Patched quests: {len(patched)}")
    print(f"Pending candidates: {len(candidates)}")
    print(f"Output: {target.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
