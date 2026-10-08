#!/usr/bin/env python3
# 📄 Dosya Yolu: /ROenglishRE/TurkuazTR/tools/validate-iteminfo-exact-strings.py
# 📌 Amac: itemInfo exact cevirilerinde Lua string kacisini ve shard guvenligini dogrular
# 📌 Modul - Tool Python
# Version: 1.0.0
# Aciklama: Tum exact shard hedeflerinin guvenli oldugunu ve tirnak korumasini test eder
# Bagimli Oldugu Katman: Tool

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = REPO_ROOT / "TurkuazTR/tools/build-iteminfo-profile.py"
spec = importlib.util.spec_from_file_location("iteminfo_builder", BUILDER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("itemInfo builder yuklenemedi")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ExactLuaStringTests(unittest.TestCase):
    def test_unescaped_double_quote_becomes_lua_escape(self) -> None:
        self.assertEqual(
            builder.escape_lua_quoted_content(b'Valkyrie "Frist" adi.'),
            b'Valkyrie \\"Frist\\" adi.',
        )

    def test_existing_escape_remains_unchanged(self) -> None:
        value = b'Valkyrie \\"Frist\\" adi.'
        self.assertEqual(builder.escape_lua_quoted_content(value), value)

    def test_dangling_backslash_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "dangling"):
            builder.escape_lua_quoted_content(b"Bad " + bytes([0x5C]))

    def test_exact_substitution_is_single_lua_string(self) -> None:
        source = r'A sword named after Valkyrie \"Frist\".'
        prepared = builder.prepare_exact_translations(
            {"translations": {source: 'Valkyrie "Frist" adi.'}}
        )
        line = ('identifiedDescriptionName = { "' + source + '", }').encode("ascii")
        counts = {}
        output = builder.apply_exact_translations(line, prepared, counts)
        self.assertEqual(counts["exact_translation"], 1)
        self.assertEqual(
            output,
            b'identifiedDescriptionName = { "Valkyrie \\"Frist\\" adi.", }',
        )

    def test_all_canonical_exact_shards_have_safe_targets(self) -> None:
        config = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-rules.json").read_text(encoding="utf-8")
        )
        shards = json.loads(
            (REPO_ROOT / "TurkuazTR/config/iteminfo-exact-shards.json").read_text(
                encoding="utf-8"
            )
        )
        paths = [config["exact_translation_path"], *shards.get("paths", [])]
        combined: dict[bytes, bytes] = {}
        for path in paths:
            records = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
            translated = builder.prepare_exact_translations(records)
            for source, target in translated.items():
                self.assertIsNotNone(
                    builder.STRING_RE.fullmatch(b'"' + target + b'"'),
                    msg=f"Invalid Lua literal: {source!r}",
                )
                self.assertNotIn(source, combined, msg=f"Duplicate exact key: {source!r}")
                combined[source] = target
        self.assertGreater(len(combined), 10000)


if __name__ == "__main__":
    unittest.main()
