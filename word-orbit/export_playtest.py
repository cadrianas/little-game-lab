#!/usr/bin/env python3
"""Inline generated puzzle data so the prototype also works as a local file."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent
template = (ROOT / "prototype.template.html").read_text()
data = (ROOT / "days.json").read_text().strip()
(ROOT / "prototype.html").write_text(template.replace("__WORD_ORBIT_DATA__", data))
print(f"Wrote {ROOT / 'prototype.html'}")
