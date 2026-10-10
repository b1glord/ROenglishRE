#!/usr/bin/env python3
# File Path: /ROenglishRE/TurkuazTR/tools/prepare-rpatchur-hybrid-test.py
# Purpose: Stage only verified 2022 Hybrid client assets and check a THOR test patch
# Module - Tool Python
# Version: 1.0.0
# Description: Does not modify original generated client files, GRF or executable
# Dependency Layer: Tool
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "TurkuazTR/generated/hybrid"
MANDATORY = (
    "SystemEN/LuaFiles514/itemInfo.lua",
    "SystemEN/Navi_Data.lub",
    "SystemEN/OngoingQuests.lub",
    "data/msgstringtable.txt",
    "data/luafiles514/lua files/skillinfoz/skillinfolist.lub",
    "data/luafiles514/lua files/skillinfoz/skilldescript.lub",
)
ALLOWED_ROOTS = {"SystemEN", "data", "tipoftheday.txt"}
THOR_MAGIC = b"ASSF (C) 2007 Aeomin DEV"
MAX_FILE_COUNT = 3000


def prepare(stage: Path, report: Path, source_sha: str) -> None:
    if not source_sha or len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise ValueError("Source commit must be a lowercase full SHA-1")
    if stage.resolve() == GENERATED.resolve():
        raise ValueError("Refusing to overwrite generated originals")
    if stage.exists():
        raise FileExistsError("Refusing to reuse a staging directory")
    stage.mkdir(parents=True)
    rows: list[dict[str, str | int]] = []
    for name in sorted(ALLOWED_ROOTS):
        src = GENERATED / name
        if not src.exists():
            continue
        paths = [src] if src.is_file() else sorted(p for p in src.rglob("*") if p.is_file())
        for path in paths:
            if path.is_symlink():
                raise ValueError("Symlink not allowed in patch payload")
            relative = path.relative_to(GENERATED)
            if relative.parts[0] not in ALLOWED_ROOTS or not all(part not in {".", ".."} for part in relative.parts):
                raise ValueError("Unsafe client path")
            if not relative.as_posix().isascii():
                raise ValueError("Non-ASCII THOR filename would be codepage-sensitive")
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            after = hashlib.sha256(target.read_bytes()).hexdigest()
            if before != after:
                raise ValueError("Staging changed source bytes")
            rows.append({"path": relative.as_posix(), "bytes": target.stat().st_size, "sha256": after})
    names = {r["path"] for r in rows}
    if not set(MANDATORY).issubset(names):
        raise ValueError("Missing required Hybrid localization files: " + repr(sorted(set(MANDATORY) - names)))
    if not rows or len(rows) > MAX_FILE_COUNT:
        raise ValueError("Unexpected file count")
    result = {
        "_file_header": {
            "path": "/ROenglishRE/dist/rpatchur/hybrid-source-manifest.json",
            "purpose": "Immutable inventory of the test patch payload",
            "module": "Generated Report - JSON",
            "version": "1.0.0",
            "description": "2022 Hybrid client files with per-file SHA-256",
            "dependency_layer": "Tool"
        },
        "channel": "2022-hybrid-test",
        "source_commit": source_sha,
        "patching_target": "client-root-loose-files",
        "grf_merge": False,
        "payload_file_count": len(rows),
        "files": rows
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"files": len(rows), "source_commit": source_sha, "grf_merge": False}))


def verify_thor(file: Path, manifest: Path) -> None:
    data = file.read_bytes()
    if not data.startswith(THOR_MAGIC):
        raise ValueError("Invalid THOR magic")
    if len(data) < 64:
        raise ValueError("THOR archive is too short")
    report = json.loads(manifest.read_text(encoding="ascii"))
    if report["grf_merge"] is not False:
        raise ValueError("Unexpected GRF merging")
    if file.stat().st_size > 100 * 1024 * 1024:
        raise ValueError("Oversized THOR test payload")
    print(json.dumps({"thor": file.name, "bytes": len(data),
                      "sha256": hashlib.sha256(data).hexdigest(),
                      "payload_files": report["payload_file_count"]}))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", type=Path)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--source-sha")
    p.add_argument("--verify-thor", type=Path)
    args = p.parse_args()
    if args.verify_thor:
        verify_thor(args.verify_thor, args.manifest)
    else:
        if not args.stage or not args.source_sha:
            p.error("--stage and --source-sha are required")
        prepare(args.stage, args.manifest, args.source_sha)


if __name__ == "__main__":
    main()
