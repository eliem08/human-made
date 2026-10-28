<!-- sell-kit:start -->
# Human Made

[![CI](https://github.com/eliem08/human-made/actions/workflows/ci.yml/badge.svg)](https://github.com/eliem08/human-made/actions/workflows/ci.yml)

> **Proof that a person wrote it, not a machine.**

**Who it's for:** Writers, publishers and schools that need to show work is human.

**The problem:** AI detectors guess and get it wrong, and writers have no way to prove they actually did the work.

**What you get:** Turn real writing-process signals into a tiered, signed certificate bound to the exact text, which anyone can verify.

## Quickstart

Customers receive a release archive with the wheel and the examples. Python 3.10+ and no other dependencies.

```bash
pip install human_made-0.1.0-py3-none-any.whl
human-made score examples/session.jsonl
human-made certify examples/session.jsonl examples/essay.txt --author "Sam Lee"
```

## Web app and API

Every command is also a JSON API endpoint and a browser form, served by the built-in web app.

```bash
human-made-web --port 8000          # then open http://127.0.0.1:8000
human-made-web keys create --label "first customer"   # prints an API key (stored hashed)
docker build -t human-made . && docker run -p 8000:8000 -e API_KEYS=sk_... -v human-made-data:/data human-made
```

Every API call needs `Authorization: Bearer <key>` once any key exists; a server on a public address refuses to start without one. Calls are rate-limited per key (60/min, `--rate`) and metered: `human-made-web usage` prints calls per key for billing.

Endpoints: `POST /api/score`, `POST /api/certify`, `POST /api/verify`, plus `GET /healthz` and `GET /api/spec` (machine-readable field list).
Files are sent as `{"name": ..., "content": ...}`, folders as `{"files": [...]}` or a base64 zip.

## Deploy and sell

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/eliem08/human-made)

`render.yaml` (one click, above) and `fly.toml` (`fly launch --copy-config`) both run the Dockerfile with a persistent `/data` volume and a `/healthz` check.
To sell self-serve, set four variables and point a Stripe webhook at `https://<your-host>/billing/webhook` (events `checkout.session.completed` and `customer.subscription.deleted`):

| Variable | Example |
|---|---|
| `STRIPE_SECRET_KEY` | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` |
| `STRIPE_PRICES` | `writer=price_123,publisher=price_456` |
| `PUBLIC_URL` | `https://human-made.example.com` |

Buyers pick a plan on `/pricing`, pay on Stripe Checkout and see their API key once on the success page. Monthly plans start with a 14-day free trial. Cancelling the subscription revokes the key. A selling server always requires a key. Education is quoted per student, so it is not a self-serve Stripe plan — contact sales for it. `.env.example` lists every variable with no values.

## Pricing

Monthly plans start with a 14-day free trial. Prices in USD, billed monthly unless noted. All plans unlock the same software in this release; higher tiers add licence scope and support, not gated features.

| Plan | Price | Includes |
|---|---|---|
| **Writer** | $6 per month | Unlimited certificates; Verification link |
| **Publisher** | $199 per month | Everything in Writer |
| **Education** | $3 per student per year | Everything in Writer; billed per student on a custom quote (contact sales, not self-serve) |

To start a trial or buy a plan, [request access](https://github.com/eliem08/human-made/issues/new?title=Human%20Made%20trial&labels=sales).

## Licence

Proprietary. Copyright (c) 2026 eliem08. All rights reserved. Use requires a paid plan or an active trial; see [LICENSE](LICENSE).
<!-- sell-kit:end -->

## What it does

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
- Plan-differentiated features: writer seats, bulk verification and article badges (Publisher); class dashboards, assignment workflows and LMS export (Education)

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
