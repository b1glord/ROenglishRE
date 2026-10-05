#!/usr/bin/env python3
# PATH: /ROenglishRE/TurkuazTR/tools/build-file-overlay-profile.py
# PURPOSE: Whole-file localization overlay bilesenlerini ortak profile gore uretir.
# MODULE-FILETYPE: Tool - Python
# VERSION: 1.0.0
# DESCRIPTION: Satir yapisi upstream ile birebir olmayan dosyalarda source blob SHA dogrular ve Turkce whole-file overlay uygular.
# DEPENDENCY-LAYER: Tool

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_FILE = REPO_ROOT / "TurkuazTR/localization-profiles.json"
REGISTRY_FILE = REPO_ROOT / "TurkuazTR/file-overlays.json"
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


def git_blob_sha(ref_name: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", f"{ref_name}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(2)
    return result.stdout.strip()


def main() -> int:
    profiles_cfg = load_json(PROFILE_FILE)
    registry_cfg = load_json(REGISTRY_FILE)
    profile_rows = profiles_cfg.get("profiles", {})
    components = registry_cfg.get("components", {})

    parser = argparse.ArgumentParser()
    parser.add_argument("--component", choices=tuple(components), required=True)
    parser.add_argument("--profile", choices=tuple(profile_rows), required=True)
    parser.add_argument("--source-ref", default=DEFAULT_SOURCE_REF)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    component = components[args.component]
    profile = profile_rows[args.profile]
    profile_field = component["profile_field"]
    mode = profile.get(profile_field, "original")
    if mode not in {"original", "tr"}:
        raise SystemExit(f"Bilinmeyen {profile_field} modu: {mode}")

    patch_cfg = load_json(REPO_ROOT / component["patch_path"])
    source_path = component["source_path"]
    if patch_cfg.get("source_path") != source_path:
        raise SystemExit(
            f"{args.component}: registry/source patch uyusmazligi: "
            f"{source_path} != {patch_cfg.get('source_path')}"
        )

    source = git_show(args.source_ref, source_path)
    actual_blob_sha = git_blob_sha(args.source_ref, source_path)
    expected_blob_sha = patch_cfg.get("source_blob_sha")
    if expected_blob_sha and actual_blob_sha != expected_blob_sha:
        raise SystemExit(
            f"{args.component}: upstream source blob degisti: "
            f"{actual_blob_sha} != {expected_blob_sha}"
        )

    if mode == "original":
        output = source
    else:
        translated = patch_cfg.get("translation_tr", "")
        try:
            output = translated.encode("ascii")
        except UnicodeEncodeError as exc:
            raise SystemExit(
                f"{args.component}: whole-file Turkce overlay ASCII degil"
            ) from exc

    output_root = args.output_root or (REPO_ROOT / "TurkuazTR/generated" / args.profile)
    output_file = output_root / component["output_path"]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(output)

    report = {
        "component": args.component,
        "profile": args.profile,
        "mode": mode,
        "source_ref": args.source_ref,
        "source_path": source_path,
        "source_blob_sha": actual_blob_sha,
        "source_size": len(source),
        "output_size": len(output),
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "output_path": component["output_path"],
    }
    report_path = output_root / f"{args.component}-build-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
