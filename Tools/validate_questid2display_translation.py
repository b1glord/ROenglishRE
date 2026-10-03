#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/Tools/validate_questid2display_translation.py
# 📌 Amac: questid2display.txt cevirisinin encoding, byte, satir sonu ve kayit yapisini dogrular
# 📌 Tool - Python
# Version: 2.0.0
# Aciklama: Patch kapsamindaki uc satir disinda kaynak blob ile birebir byte esitligi ister; satir sonu degisimini ve ASCII disi patch byte'ini reddeder
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HEADER_RE = re.compile(rb"^(\d+)#([^#]*)#([^#]*)#([^#]*)#$")


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


def structural_line(line: bytes) -> bytes:
    body, _ = split_content_and_eol(line)
    match = HEADER_RE.match(body)
    if match:
        quest_id, _title, icon, image = match.groups()
        return quest_id + b"##" + icon + b"#" + image + b"#"
    if body == b"":
        return b""
    if body.endswith(b"#"):
        return b"#"
    return body


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate encoding-safe questid2display localization."
    )
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

    allowed_indexes: set[int] = set()
    patched_headers: set[str] = set()
    for index, raw_line in enumerate(upstream):
        body, _ = split_content_and_eol(raw_line)
        match = HEADER_RE.match(body)
        if not match:
            continue
        quest_id = match.group(1).decode("ascii")
        if quest_id in patch_ids:
            allowed_indexes.update({index, index + 1, index + 2})
            patched_headers.add(quest_id)

    missing = sorted(patch_ids - patched_headers, key=int)
    if missing:
        print(
            "Upstream dosyada bulunamayan patch quest ID'leri: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    changed_lines = 0
    for index, (source, target) in enumerate(zip(upstream, translated), start=1):
        source_body, source_eol = split_content_and_eol(source)
        target_body, target_eol = split_content_and_eol(target)

        if source_eol != target_eol:
            print(f"Satir sonu degisti: satir {index}", file=sys.stderr)
            return 1

        if structural_line(source) != structural_line(target):
            print(f"Quest yapisi degisti: satir {index}", file=sys.stderr)
            return 1

        zero_index = index - 1
        if zero_index not in allowed_indexes and source != target:
            print(f"Patch disi byte degisikligi bulundu: satir {index}", file=sys.stderr)
            return 1

        if source != target:
            changed_lines += 1
            if any(byte >= 0x80 for byte in target_body):
                print(
                    f"Degistirilen quest satirinda ASCII disi byte bulundu: satir {index}",
                    file=sys.stderr,
                )
                return 1

    print("questid2display encoding-safe byte structure: OK")
    print(f"Patch quest count: {len(patch_ids)}")
    print(f"Changed lines: {changed_lines}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
