#!/usr/bin/env python3
# Dosya Yolu: /ROenglishRE/Tools/apply_ongoingquests_translation.py
# Amac: OngoingQuests.lub guvenli alanlarini byte-safe Turkce patch ile gunceller
# Modul: Tool - Python
# Version: 1.4.0
# Aciklama: Title/Summary, guvenli Description ve NAVI/ITEM byte dizilerini birebir koruyan sablonlu Description cevirilerini uygular
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
DESCRIPTION_START_RE = re.compile(rb"^\s*Description\s*=\s*\{\s*$")
DESCRIPTION_VALUE_RE = re.compile(rb'^(\s*")(.*)("[,]?\s*)$')
DESCRIPTION_END_RE = re.compile(rb"^\s*\}[,]?\s*$")
PROTECTED_PATTERNS = {
    "NAVI": re.compile(rb"<NAVI>.*?</NAVI>"),
    "ITEM": re.compile(rb"<ITEM>.*?</ITEM>"),
}
PLACEHOLDER_RE = re.compile(rb"\{\{(NAVI|ITEM)(\d+)\}\}")


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


def ascii_lua_fragment(value: bytes) -> bytes:
    return value.replace(b"\\", b"\\\\").replace(b'"', b'\\"')


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


def description_index(lines: list[bytes], start: int, end: int) -> tuple[int | None, str]:
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
        return None, "description-block-missing"

    values: list[int] = []
    for index in range(block_start + 1, block_end):
        body, _ = split_content_and_eol(lines[index])
        if DESCRIPTION_VALUE_RE.match(body):
            values.append(index)
        elif body.strip():
            return None, "description-structure-complex"
    if len(values) != 1:
        return None, "description-multiline"
    return values[0], "single-line"


def protected_spans(source_value: bytes) -> dict[str, list[bytes]]:
    return {
        tag: pattern.findall(source_value)
        for tag, pattern in PROTECTED_PATTERNS.items()
    }


def render_protected_template(template: str, source_value: bytes, quest_id: str) -> bytes:
    try:
        template_bytes = template.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{quest_id}.ongoing_description: ASCII disi karakter var") from exc

    spans = protected_spans(source_value)
    used: dict[str, list[int]] = {tag: [] for tag in PROTECTED_PATTERNS}
    for tag_bytes, index_bytes in PLACEHOLDER_RE.findall(template_bytes):
        tag = tag_bytes.decode("ascii")
        used[tag].append(int(index_bytes))

    for tag, values in spans.items():
        expected = list(range(1, len(values) + 1))
        if used[tag] != expected:
            raise ValueError(
                f"{quest_id}.ongoing_description: {tag} placeholders {used[tag]}, beklenen {expected}"
            )

    output = bytearray()
    cursor = 0
    for match in PLACEHOLDER_RE.finditer(template_bytes):
        output.extend(ascii_lua_fragment(template_bytes[cursor:match.start()]))
        tag = match.group(1).decode("ascii")
        span_index = int(match.group(2)) - 1
        output.extend(spans[tag][span_index])
        cursor = match.end()
    output.extend(ascii_lua_fragment(template_bytes[cursor:]))
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply byte-safe OngoingQuests translations.")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--path", default="Translation/Renewal/SystemEN/OngoingQuests.lub")
    parser.add_argument("--patch", default="TurkuazTR/questid2display.tr.json")
    parser.add_argument("--output-path", default=None)
    parser.add_argument("--source-ref", default="refs/remotes/origin/upstream/latest")
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
    description_patched = 0
    protected_description_patched = 0
    description_skipped: dict[str, int] = {}
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
            output_lines[index] = match.group(1) + replacement + match.group(4) + eol
            seen.add(field)
            if output_lines[index] != source_lines[index]:
                changed_lines += 1

        if b"Title" not in seen:
            raise ValueError(f"{quest_id}: Title alani bulunamadi")

        desc_index, reason = description_index(source_lines, start, end)
        if desc_index is not None:
            body, eol = split_content_and_eol(source_lines[desc_index])
            match = DESCRIPTION_VALUE_RE.match(body)
            if match is None:
                raise ValueError(f"{quest_id}: Description satiri ayrisitirilamadi")

            source_value = match.group(2)
            spans = protected_spans(source_value)
            has_protected = any(spans.values())

            if has_protected:
                template = patch.get("ongoing_description")
                if template:
                    replacement = render_protected_template(template, source_value, quest_id)
                    output_lines[desc_index] = match.group(1) + replacement + match.group(3) + eol
                    if output_lines[desc_index] != source_lines[desc_index]:
                        changed_lines += 1
                        description_patched += 1
                        protected_description_patched += 1
                else:
                    reason = "description-has-protected-tags"
                    description_skipped[reason] = description_skipped.get(reason, 0) + 1
            else:
                replacement = ascii_lua_string(
                    patch.get("description", ""),
                    quest_id,
                    "description",
                )
                output_lines[desc_index] = match.group(1) + replacement + match.group(3) + eol
                if output_lines[desc_index] != source_lines[desc_index]:
                    changed_lines += 1
                    description_patched += 1
        else:
            description_skipped[reason] = description_skipped.get(reason, 0) + 1

        applied_records += 1

    if len(output_lines) != len(source_lines):
        print("Satir sayisi degisti.", file=sys.stderr)
        return 1

    for index, (before, after) in enumerate(zip(source_lines, output_lines), start=1):
        if before == after:
            continue
        _, before_eol = split_content_and_eol(before)
        _, after_eol = split_content_and_eol(after)
        if before_eol != after_eol:
            print(f"Satir sonu degisti: satir {index}", file=sys.stderr)
            return 1

    target = Path(args.output_path).resolve() if args.output_path else (repo_root / args.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"".join(output_lines))

    print(f"Patch config records: {len(patches)}")
    print(f"OngoingQuests matched records: {applied_records}")
    print(f"Changed translation lines: {changed_lines}")
    print(f"Description lines patched: {description_patched}")
    print(f"Protected-tag Description lines patched: {protected_description_patched}")
    print(f"Missing OngoingQuests records: {len(missing_records)}")
    for skip_reason, count in sorted(description_skipped.items()):
        print(f"Skipped {skip_reason}: {count}")
    if missing_records:
        print("Missing IDs: " + ", ".join(sorted(missing_records, key=int)[:50]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
