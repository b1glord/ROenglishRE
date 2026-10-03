#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/Tools/validate_ongoingquests_translation.py
# 📌 Amac: OngoingQuests.lub guvenli alan cevirilerinin byte-safe kapsamda kaldigini dogrular
# 📌 Tool - Python
# Version: 1.1.0
# Aciklama: Hedef questlerde Title, Summary ve yalnizca guvenli tek satirli NAVI etiketsiz Description degisikliklerine izin verir
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
DESCRIPTION_START_RE = re.compile(rb"^\s*Description\s*=\s*\{\s*$")
DESCRIPTION_VALUE_RE = re.compile(rb'^\s*"(.*)"[,]?\s*$')
DESCRIPTION_END_RE = re.compile(rb"^\s*\}[,]?\s*$")
NAVI_MARKERS = (b"<NAVI>", b"<INFO>", b"</NAVI>", b"</INFO>")


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


def record_ranges(lines: list[bytes]) -> dict[str, tuple[int, int]]:
    starts: list[tuple[str, int]] = []
    for index, raw_line in enumerate(lines):
        body, _ = split_content_and_eol(raw_line)
        match = RECORD_RE.match(body)
        if match:
            starts.append((match.group(1).decode("ascii"), index))

    result: dict[str, tuple[int, int]] = {}
    for offset, (quest_id, start) in enumerate(starts):
        end = starts[offset + 1][1] if offset + 1 < len(starts) else len(lines)
        result[quest_id] = (start, end)
    return result


def safe_description_index(
    lines: list[bytes],
    start: int,
    end: int,
) -> int | None:
    description_start: int | None = None
    description_end: int | None = None

    for index in range(start, end):
        body, _ = split_content_and_eol(lines[index])
        if description_start is None:
            if DESCRIPTION_START_RE.match(body):
                description_start = index
            continue

        if DESCRIPTION_END_RE.match(body):
            description_end = index
            break

    if description_start is None or description_end is None:
        return None

    value_indexes: list[int] = []
    for index in range(description_start + 1, description_end):
        body, _ = split_content_and_eol(lines[index])
        match = DESCRIPTION_VALUE_RE.match(body)
        if match:
            value_indexes.append(index)
        elif body.strip():
            return None

    if len(value_indexes) != 1:
        return None

    body, _ = split_content_and_eol(lines[value_indexes[0]])
    match = DESCRIPTION_VALUE_RE.match(body)
    if match is None:
        return None

    source_value = match.group(1)
    if any(marker in source_value for marker in NAVI_MARKERS):
        return None

    return value_indexes[0]


def allowed_indexes(lines: list[bytes], patch_ids: set[str]) -> set[int]:
    allowed: set[int] = set()
    ranges = record_ranges(lines)

    for quest_id in patch_ids:
        record_range = ranges.get(quest_id)
        if record_range is None:
            continue

        start, end = record_range
        for index in range(start, end):
            body, _ = split_content_and_eol(lines[index])
            if FIELD_RE.match(body):
                allowed.add(index)

        description_index = safe_description_index(lines, start, end)
        if description_index is not None:
            allowed.add(description_index)

    return allowed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate byte-safe OngoingQuests translations."
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
            print(f"Izinli alan disi byte degisikligi: satir {index + 1}", file=sys.stderr)
            return 1

        _, source_eol = split_content_and_eol(source)
        target_body, target_eol = split_content_and_eol(target)
        if source_eol != target_eol:
            print(f"Satir sonu degisti: satir {index + 1}", file=sys.stderr)
            return 1

        if any(byte >= 0x80 for byte in target_body):
            print(f"Degisen satirda ASCII disi byte var: satir {index + 1}", file=sys.stderr)
            return 1

        changed += 1

    print("OngoingQuests byte-safe translation validation: OK")
    print(f"Allowed translation lines: {len(allowed)}")
    print(f"Changed lines: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
