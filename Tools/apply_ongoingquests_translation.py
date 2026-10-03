#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/Tools/apply_ongoingquests_translation.py
# 📌 Amac: OngoingQuests.lub icinde Title ve Summary alanlarini byte-safe Turkce patch ile gunceller
# 📌 Tool - Python
# Version: 1.0.0
# Aciklama: Description ve NAVI alanlarina dokunmaz; kaynak byte yapisini ve satir sonlarini korur
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RECORD_RE = re.compile(rb"^\s*\[(\d+)\]\s*=\s*\{\s*$")
FIELD_RE = re.compile(rb'^(\s*(Title|Summary)\s*=\s*")(.*)("[,]?\s*)$')


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


def ascii_lua_string(value: str, quest_id: str, field: str) -> bytes:
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{quest_id}.{field}: ASCII disi karakter var") from exc
    return encoded.replace(b"\\", b"\\\\").replace(b'"', b'\\"')


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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply byte-safe OngoingQuests Title/Summary translations."
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
        "--source-ref",
        default="refs/remotes/origin/upstream/latest",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else script_path.parent.parent

    patch_cfg = json.loads((repo_root / args.patch).read_text(encoding="utf-8"))
    patches = patch_cfg["patches"]

    source = git_show(repo_root, args.source_ref, args.path)
    source_lines = source.splitlines(keepends=True)
    output_lines = list(source_lines)
    ranges = record_ranges(source_lines)

    applied_records = 0
    changed_lines = 0
    missing_records: list[str] = []

    for quest_id, patch in patches.items():
        record_range = ranges.get(quest_id)
        if record_range is None:
            missing_records.append(quest_id)
            continue

        start, end = record_range
        requested = {
            b"Title": ascii_lua_string(patch["title"], quest_id, "title"),
            b"Summary": ascii_lua_string(patch.get("goal", ""), quest_id, "goal"),
        }
        seen: set[bytes] = set()

        for index in range(start, end):
            body, eol = split_content_and_eol(source_lines[index])
            match = FIELD_RE.match(body)
            if not match:
                continue

            field = match.group(2)
            replacement = requested.get(field)
            if replacement is None:
                continue

            new_body = match.group(1) + replacement + match.group(4)
            output_lines[index] = new_body + eol
            seen.add(field)
            if output_lines[index] != source_lines[index]:
                changed_lines += 1

        if b"Title" not in seen:
            raise ValueError(f"{quest_id}: Title alani bulunamadi")

        applied_records += 1

    if len(output_lines) != len(source_lines):
        print("Satir sayisi degisti.", file=sys.stderr)
        return 1

    for index, (before, after) in enumerate(zip(source_lines, output_lines), start=1):
        if before == after:
            continue
        _, before_eol = split_content_and_eol(before)
        after_body, after_eol = split_content_and_eol(after)
        if before_eol != after_eol:
            print(f"Satir sonu degisti: satir {index}", file=sys.stderr)
            return 1
        if any(byte >= 0x80 for byte in after_body):
            print(f"Patch satirinda ASCII disi byte var: satir {index}", file=sys.stderr)
            return 1

    target = repo_root / args.path
    target.write_bytes(b"".join(output_lines))

    print(f"Patch config records: {len(patches)}")
    print(f"OngoingQuests matched records: {applied_records}")
    print(f"Changed Title/Summary lines: {changed_lines}")
    print(f"Missing OngoingQuests records: {len(missing_records)}")
    if missing_records:
        print("Missing IDs: " + ", ".join(sorted(missing_records, key=int)[:50]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
