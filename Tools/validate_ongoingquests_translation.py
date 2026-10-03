#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/Tools/validate_ongoingquests_translation.py
# 📌 Amac: OngoingQuests.lub Title ve Summary cevirilerinin byte-safe kapsamda kaldigini dogrular
# 📌 Tool - Python
# Version: 1.0.0
# Aciklama: Hedef questlerin Title/Summary satirlari disinda kaynak blob ile birebir byte esitligi ister
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RECORD_RE = re.compile(rb"^\s*\[(\d+)\]\s*=\s*\{\s*$")
FIELD_RE = re.compile(rb'^\s*(Title|Summary)\s*=\s*".*"[,]?\s*$')


def git_show(repo_root: Path, ref_name: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref_name}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(2)
    return result.stdout


def split_content_and_eol(line: bytes) -> tuple[bytes, bytes]:
    if line.endswith(b"\r\n"):
        return line[:-2], b"\r\n"
    if line.endswith(b"\n"):
        return line[:-1], b"\n"
    if line.endswith(b"\r"):
        return line[:-1], b"\r"
    return line, b""


def allowed_indexes(lines: list[bytes], patch_ids: set[str]) -> set[int]:
    allowed: set[int] = set()
    current_id: str | None = None

    for index, raw_line in enumerate(lines):
        body, _ = split_content_and_eol(raw_line)
        record_match = RECORD_RE.match(body)
        if record_match:
            current_id = record_match.group(1).decode("ascii")
            continue

        if current_id in patch_ids and FIELD_RE.match(body):
            allowed.add(index)

    return allowed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate byte-safe OngoingQuests Title/Summary translations."
    )
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--path",
        default="Translation/Renewal/SystemEN/OngoingQuests.lub",
    )
    parser.add_argument(
        "--patch",
        default="TurkuazTR/questid2display.tr.json",
    )
    parser.add_argument(
        "--upstream-ref",
        default="refs/remotes/origin/upstream/latest",
    )
    parser.add_argument("--translation-ref", default="HEAD")
    parser.add_argument("--working-tree", action="store_true")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else script_path.parent.parent

    patch_cfg = json.loads((repo_root / args.patch).read_text(encoding="utf-8"))
    patch_ids = set(patch_cfg["patches"])

    upstream_raw = git_show(repo_root, args.upstream_ref, args.path)
    translated_raw = (
        (repo_root / args.path).read_bytes()
        if args.working_tree
        else git_show(repo_root, args.translation_ref, args.path)
    )

    upstream = upstream_raw.splitlines(keepends=True)
    translated = translated_raw.splitlines(keepends=True)

    if len(upstream) != len(translated):
        print(
            f"Satir sayisi farkli: upstream={len(upstream)}, translation={len(translated)}",
            file=sys.stderr,
        )
        return 1

    allowed = allowed_indexes(upstream, patch_ids)
    changed = 0

    for index, (source, target) in enumerate(zip(upstream, translated)):
        if source == target:
            continue

        if index not in allowed:
            print(f"Title/Summary disi byte degisikligi: satir {index + 1}", file=sys.stderr)
            return 1

        _, source_eol = split_content_and_eol(source)
        target_body, target_eol = split_content_and_eol(target)
        if source_eol != target_eol:
            print(f"Satir sonu degisti: satir {index + 1}", file=sys.stderr)
            return 1

        if any(byte >= 0x80 for byte in target_body):
            print(f"Degisen satirda ASCII disi byte var: satir {index + 1}", file=sys.stderr)
            return 1

        if not FIELD_RE.match(target_body):
            print(f"Title/Summary yapisi bozuldu: satir {index + 1}", file=sys.stderr)
            return 1

        changed += 1

    print("OngoingQuests byte-safe Title/Summary validation: OK")
    print(f"Allowed Title/Summary lines: {len(allowed)}")
    print(f"Changed lines: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
