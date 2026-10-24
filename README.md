# human-made

[![CI](https://github.com/eliem08/human-made/actions/workflows/ci.yml/badge.svg)](https://github.com/eliem08/human-made/actions/workflows/ci.yml)

> **The organic label for human-made content** — proof a person made it.

AI detectors guess from the finished text and are wrong constantly. The
better signal is *how* the text was made: humans type in bursts, pause,
delete, rewrite; pasted-in machine output arrives in one block. `human-made`
records the writing process, scores it, and issues a signed, verifiable
"Human-made" label bound to the exact final text.

## What the MVP does

- **Process log** (JSONL) from an editor plugin: `{t, type: insert|delete|paste, n, pos}`
- **Signals**:
  - paste ratio — pasted characters / final characters
  - revision ratio — deleted / inserted characters
  - typing cadence — coefficient of variation of inter-keystroke intervals
    (humans are irregular; replayed / scripted input is metronomic)
  - pauses — share of gaps > 2 s (thinking time)
  - throughput — characters per active minute vs. human typing range
- **Verdict tiers**: `human-made`, `human-led` (some assisted/pasted input), `unverified`
- **Certificate**: HMAC-signed JSON binding SHA-256(final text) + tier + signal summary + timestamp
- **Verify**: anyone with the verification key checks that a text matches its label
  (changing one character breaks it)

## Quickstart

```bash
pip install -e .
human-made score examples/session.jsonl
human-made certify examples/session.jsonl examples/essay.txt --author "Sam Lee" > cert.json
human-made verify cert.json examples/essay.txt
```

## Roadmap

- Editor plugins (VS Code, Google Docs, Obsidian) emitting the process log
- Public-key signatures (Ed25519) and C2PA manifest embedding
- Process replay viewer for disputes, privacy-preserving (no keystroke content stored)

## Development

Zero runtime dependencies; Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m unittest discover -s tests -t .           # unit + CLI smoke tests
ruff check . && ruff format --check .               # lint + format
```

```
human_made/core.py       domain logic (pure, importable, fully tested)
human_made/__main__.py   CLI (`human-made ...` / `python -m human_made ...`)
tests/                unit tests + generated CLI smoke tests
examples/             sample inputs used by the docs and smoke tests
```

CI runs lint and tests on Ubuntu and Windows across Python 3.10, 3.12 and 3.13.
Design, data model, trade-offs and production path: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

Part of the [agent-economy](https://github.com/eliem08/agent-economy) portfolio (idea #35).
