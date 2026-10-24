"""Regenerate examples/session.jsonl from examples/essay.txt."""

import json
import pathlib

from human_made import synthetic_session

here = pathlib.Path(__file__).parent
text = (here / "essay.txt").read_text(encoding="utf-8").rstrip("\n") + "\n"
with open(here / "session.jsonl", "w", encoding="utf-8") as fh:
    for e in synthetic_session(text):
        fh.write(json.dumps(e) + "\n")
