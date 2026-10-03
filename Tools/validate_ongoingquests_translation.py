#!/usr/bin/env python3
# Dosya Yolu: /ROenglishRE/Tools/validate_ongoingquests_translation.py
# Amac: OngoingQuests.lub byte-safe ceviri kapsamlarini ve NAVI byte korumasini dogrular
# Modul: Tool - Python
# Version: 1.2.0
# Aciklama: Title/Summary, guvenli Description ve sablonla etkinlestirilen NAVI Description satirlarina izin verir; NAVI spanlarini birebir karsilastirir
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
NAVI_SPAN_RE = re.compile(rb"<NAVI>.*?</NAVI>")


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
    return {
        quest_id: (
            start,
            starts[offset + 1][1] if offset + 1 < len(starts) else len(lines),
        )
        for offset, (quest_id, start) in enumerate(starts)
    }


def description_index(lines: list[bytes], start: int, end: int) -> int | None:
    block_start: int | None = None
    block_end: int | None = None
    for index in range(start, end):
        body, _ = split_content_and_eol(lines[index])
        if block_start is None:
            if DESCRIPTION_START_RE.match(body):
                block_start = index
            continue
        if DESCRIPTION_END_RE.match(body):
            block_end = index
            break

    if block_start is None or block_end is None:
        return None

    values: list[int] = []
    for index in range(block_start + 1, block_end):
        body, _ = split_content_and_eol(lines[index])
        if DESCRIPTION_VALUE_RE.match(body):
            values.append(index)
        elif body.strip():
            return None
    return values[0] if len(values) == 1 else None


def allowed_indexes(
    lines: list[bytes],
    patches: dict[str, dict[str, str]],
) -> tuple[set[int], dict[int, bool]]:
    allowed: set[int] = set()
    navi_required: dict[int, bool] = {}
    ranges = record_ranges(lines)

    for quest_id, patch in patches.items():
        record_range = ranges.get(quest_id)
        if record_range is None:
            continue
        start, end = record_range

        for index in range(start, end):
            body, _ = split_content_and_eol(lines[index])
            if FIELD_RE.match(body):
                allowed.add(index)

        desc_index = description_index(lines, start, end)
        if desc_index is None:
            continue

        body, _ = split_content_and_eol(lines[desc_index])
        match = DESCRIPTION_VALUE_RE.match(body)
        if match is None:
            continue

        has_navi = bool(NAVI_SPAN_RE.findall(match.group(1)))
        if not has_navi or patch.get("ongoing_description"):
            allowed.add(desc_index)
            navi_required[desc_index] = has_navi

    return allowed, navi_required


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate byte-safe OngoingQuests translations.")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--path", default="Translation/Renewal/SystemEN/OngoingQuests.lub")
    parser.add_argument("--patch", default="TurkuazTR/questid2display.tr.json")
    parser.add_argument("--upstream-ref", default="refs/remotes/origin/upstream/latest")
    parser.add_argument("--translation-ref", default="HEAD")
    parser.add_argument("--working-tree", action="store_true")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else script_path.parent.parent
    patch_cfg = json.loads((repo_root / args.patch).read_text(encoding="utf-8"))
    patches = patch_cfg["patches"]

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

    allowed, navi_required = allowed_indexes(upstream, patches)
    changed = 0
    verified_navi = 0

    for index, (source, target) in enumerate(zip(upstream, translated)):
        if source == target:
            continue
        if index not in allowed:
            print(f"Izinli alan disi byte degisikligi: satir {index + 1}", file=sys.stderr)
            return 1

        source_body, source_eol = split_content_and_eol(source)
        target_body, target_eol = split_content_and_eol(target)
        if source_eol != target_eol:
            print(f"Satir sonu degisti: satir {index + 1}", file=sys.stderr)
            return 1

        if navi_required.get(index):
            source_match = DESCRIPTION_VALUE_RE.match(source_body)
            target_match = DESCRIPTION_VALUE_RE.match(target_body)
            if source_match is None or target_match is None:
                print(f"NAVI Description yapisi bozuldu: satir {index + 1}", file=sys.stderr)
                return 1
            source_spans = NAVI_SPAN_RE.findall(source_match.group(1))
            target_spans = NAVI_SPAN_RE.findall(target_match.group(1))
            if source_spans != target_spans:
                print(f"NAVI byte dizisi degisti: satir {index + 1}", file=sys.stderr)
                return 1
            verified_navi += 1

        changed += 1

    print("OngoingQuests byte-safe translation validation: OK")
    print(f"Allowed translation lines: {len(allowed)}")
    print(f"Changed lines: {changed}")
    print(f"Verified NAVI Description lines: {verified_navi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
