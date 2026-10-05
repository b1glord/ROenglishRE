#!/usr/bin/env python3
# PATH: /ROenglishRE/TurkuazTR/tools/build-msgstringtable-profile.py
# PURPOSE: Ortak localization profiline gore msgstringtable generated ciktilarini uretir.
# MODULE-FILETYPE: Tool - Python
# VERSION: 1.0.0
# DESCRIPTION: upstream/latest Ingilizce kaynagi exact-source Turkce overlay ile byte-safe birlestirir.
# DEPENDENCY-LAYER: Tool

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_FILE = REPO_ROOT / "TurkuazTR/localization-profiles.json"
PATCH_FILE = REPO_ROOT / "TurkuazTR/msgstringtable.tr.json"
DEFAULT_SOURCE_PATH = "Translation/Renewal/data/msgstringtable.txt"
DEFAULT_SOURCE_REF = "refs/remotes/origin/upstream/latest"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_show(ref_name: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{ref_name}:{path}"],
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


def main() -> int:
    profiles = load_json(PROFILE_FILE)
    profile_rows = profiles.get("profiles", {})

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=tuple(profile_rows), required=True)
    parser.add_argument("--source-ref", default=DEFAULT_SOURCE_REF)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    profile = profile_rows[args.profile]
    mode = profile.get("msgstringtable", "original")
    if mode not in {"original", "tr"}:
        raise SystemExit(f"Bilinmeyen msgstringtable modu: {mode}")

    patch_cfg = load_json(PATCH_FILE)
    source_path = patch_cfg.get("source_path", DEFAULT_SOURCE_PATH)
    source = git_show(args.source_ref, source_path)
    source_lines = source.splitlines(keepends=True)

    expected_line_count = patch_cfg.get("source_line_count")
    if expected_line_count is not None and len(source_lines) != expected_line_count:
        raise SystemExit(
            f"msgstringtable satir sayisi degisti: {len(source_lines)} != {expected_line_count}"
        )

    output_lines = list(source_lines)
    applied = 0
    stale: list[str] = []

    if mode == "tr":
        for line_key, patch in patch_cfg.get("patches", {}).items():
            line_no = int(line_key)
            index = line_no - 1
            if index < 0 or index >= len(source_lines):
                stale.append(f"{line_no}:satir-yok")
                continue

            body, eol = split_content_and_eol(source_lines[index])
            try:
                source_text = body.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SystemExit(f"{line_no}: UTF-8 decode hatasi") from exc

            expected = patch.get("source_en", "")
            if source_text != expected:
                stale.append(f"{line_no}:source-degisti")
                continue

            translated = patch.get("translation_tr", "")
            try:
                translated_bytes = translated.encode("ascii")
            except UnicodeEncodeError as exc:
                raise SystemExit(f"{line_no}: Turkce patch ASCII degil") from exc

            output_lines[index] = translated_bytes + eol
            applied += 1

        expected_patch_count = patch_cfg.get("patch_count", len(patch_cfg.get("patches", {})))
        if applied != expected_patch_count or stale:
            preview = ", ".join(stale[:20])
            raise SystemExit(
                f"msgstringtable overlay stale: applied={applied}, expected={expected_patch_count}, stale={preview}"
            )

    output = b"".join(output_lines)
    output_root = args.output_root or (REPO_ROOT / "TurkuazTR/generated" / args.profile)
    output_file = output_root / "data/msgstringtable.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(output)

    report = {
        "profile": args.profile,
        "mode": mode,
        "source_ref": args.source_ref,
        "source_path": source_path,
        "source_line_count": len(source_lines),
        "patch_count": patch_cfg.get("patch_count", 0),
        "applied_patch_count": applied,
        "stale_patch_count": len(stale),
    }
    (output_root / "msgstringtable-build-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
