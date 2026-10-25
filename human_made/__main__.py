import argparse
import csv
import json
import os
import sys

from .core import analyze, certify, verdict, verify


def _events(path):
    with open(path, encoding="utf-8-sig") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def _text(path):
    with open(path, encoding="utf-8-sig") as fh:
        return fh.read()


def _run(argv=None):
    ap = argparse.ArgumentParser(prog="human-made")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score")
    s.add_argument("session")
    c = sub.add_parser("certify")
    c.add_argument("session")
    c.add_argument("text")
    c.add_argument("--author", required=True)
    v = sub.add_parser("verify")
    v.add_argument("cert")
    v.add_argument("text")
    a = ap.parse_args(argv)
    if a.cmd == "score":
        sig = analyze(_events(a.session))
        tier, reasons = verdict(sig)
        print(f"Label: {tier.upper()}")
        for k, val in sig.__dict__.items():
            print(f"  {k:<22} {val}")
        for r in reasons:
            print(f"  - {r}")
        return 0
    if a.cmd == "certify":
        print(json.dumps(certify(_events(a.session), _text(a.text), a.author), indent=2))
        return 0
    with open(a.cert, encoding="utf-8-sig") as fh:
        ok, msg = verify(json.load(fh), _text(a.text))
    print(("VALID: " if ok else "INVALID: ") + msg)
    return 0 if ok else 2


def main(argv=None):
    """Run the CLI; a bad input file or argument exits 2 with a one-line error instead of a traceback.

    Set AGENT_ECONOMY_DEBUG=1 to see the full traceback.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    try:
        return _run(argv)
    except (OSError, ValueError, KeyError, csv.Error) as e:
        if os.environ.get("AGENT_ECONOMY_DEBUG"):
            raise
        msg = e.args[0] if isinstance(e, KeyError) and e.args else e
        print(f"error: {msg}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
