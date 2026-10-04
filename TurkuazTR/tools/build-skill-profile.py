#!/usr/bin/env python3
# PATH: /ROenglishRE/TurkuazTR/tools/build-skill-profile.py
# PURPOSE: Hybrid ve Full TR skill paketlerini ortak patch kaynaklarindan uretir.
# MODULE-FILETYPE: Tool - Python
# VERSION: 1.0.0
# DESCRIPTION: SkillName ve skill description patchlerini uygular; kaynak description encodingini korur.
# DEPENDENCY-LAYER: Tool

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INFO_SOURCE = REPO_ROOT / "Translation/Renewal/data/luafiles514/lua files/skillinfoz/skillinfolist.lub"
DESC_SOURCE = REPO_ROOT / "Translation/Renewal/data/luafiles514/lua files/skillinfoz/skilldescript.lub"
NAME_PATCH = REPO_ROOT / "TurkuazTR/skillinfolist.tr.json"
DESC_PATCH = REPO_ROOT / "TurkuazTR/skilldescript.tr.json"
PROFILE_FILE = REPO_ROOT / "TurkuazTR/skill-profiles.json"

INFO_NAME_RE = re.compile(
    r'(\[SKID\.([A-Z0-9_]+)\]\s*=\s*\{.*?SkillName\s*=\s*")([^"]*)(")',
    re.S,
)
BLOCK_START_RE = re.compile(r"\[SKID\.([A-Z0-9_]+)\]\s*=\s*\{")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text_with_encoding(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Desteklenmeyen encoding: {path}")


def lua_quote(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def choose_name(name_patch: dict, key: str, profile: str) -> str | None:
    row = name_patch.get("patches", {}).get(key)
    if not row:
        return None
    if profile == "hybrid":
        return row.get("name_original")
    return row.get("name_tr")


def apply_skill_names(text: str, name_patch: dict, profile: str) -> str:
    def repl(match: re.Match[str]) -> str:
        selected = choose_name(name_patch, match.group(2), profile)
        if not selected:
            return match.group(0)
        return f"{match.group(1)}{selected}{match.group(4)}"

    return INFO_NAME_RE.sub(repl, text)


def split_blocks(text: str) -> list[tuple[int, int, str]]:
    starts = list(BLOCK_START_RE.finditer(text))
    result: list[tuple[int, int, str]] = []
    for index, match in enumerate(starts):
        start = match.start()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        result.append((start, end, match.group(1)))
    return result


def render_description_block(key: str, name: str, lines: list[str]) -> str:
    values = [name, *lines]
    body = ",\n".join(f"\t\t{lua_quote(value)}" for value in values)
    return f"[SKID.{key}] = {{\n{body}\n\t}},\n\t"


def apply_skill_descriptions(
    text: str,
    name_patch: dict,
    desc_patch: dict,
    profile: str,
) -> tuple[str, list[str]]:
    patches = desc_patch.get("patches", {})
    blocks = split_blocks(text)
    block_map = {key: (start, end) for start, end, key in blocks}
    missing = [key for key in patches if key not in block_map]

    replacements: list[tuple[int, int, str]] = []
    for key, patch in patches.items():
        if key not in block_map:
            continue
        start, end = block_map[key]
        selected_name = (
            choose_name(name_patch, key, profile)
            or patch.get("name_original")
            or key
        )
        lines = patch.get("lines_tr", [])
        replacements.append((start, end, render_description_block(key, selected_name, lines)))

    for start, end, rendered in sorted(replacements, reverse=True):
        text = text[:start] + rendered + text[end:]

    return text, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("hybrid", "full_tr"), required=True)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    profiles = load_json(PROFILE_FILE)
    if args.profile not in profiles.get("profiles", {}):
        raise SystemExit(f"Bilinmeyen profil: {args.profile}")

    name_patch = load_json(NAME_PATCH)
    desc_patch = load_json(DESC_PATCH)

    info_text = INFO_SOURCE.read_text(encoding="utf-8")
    desc_text, desc_encoding = read_text_with_encoding(DESC_SOURCE)

    generated_info = apply_skill_names(info_text, name_patch, args.profile)
    generated_desc, missing = apply_skill_descriptions(
        desc_text,
        name_patch,
        desc_patch,
        args.profile,
    )

    output_root = args.output_root or (REPO_ROOT / "TurkuazTR/generated" / args.profile)
    output_dir = output_root / "data/luafiles514/lua files/skillinfoz"
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "skillinfolist.lub").write_text(
        generated_info,
        encoding="utf-8",
        newline="",
    )
    (output_dir / "skilldescript.lub").write_bytes(
        generated_desc.encode(desc_encoding, errors="strict")
    )

    report = {
        "profile": args.profile,
        "source_description_encoding": desc_encoding,
        "name_patch_count": len(name_patch.get("patches", {})),
        "description_patch_count": len(desc_patch.get("patches", {})),
        "missing_description_keys": missing,
    }
    (output_root / "skill-build-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    if missing:
        raise SystemExit(f"Eksik description bloklari: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
