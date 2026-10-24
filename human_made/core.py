"""Writing-process signals, verdict tiers and signed human-made certificates."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

__all__ = ["Signals", "analyze", "verdict", "certify", "verify", "synthetic_session"]


@dataclass
class Signals:
    typed_chars: int
    pasted_chars: int
    deleted_chars: int
    final_chars: int
    paste_ratio: float
    revision_ratio: float
    cadence_cv: float
    pause_share: float
    chars_per_active_min: float
    duration_s: float


def analyze(events: list[dict]) -> Signals:
    events = sorted(events, key=lambda e: e["t"])
    typed = sum(e.get("n", 1) for e in events if e["type"] == "insert")
    pasted = sum(e.get("n", 0) for e in events if e["type"] == "paste")
    deleted = sum(e.get("n", 1) for e in events if e["type"] == "delete")
    final = max(0, typed + pasted - deleted)
    key_times = [e["t"] for e in events if e["type"] in ("insert", "delete")]
    gaps = [b - a for a, b in zip(key_times, key_times[1:]) if b > a]
    short = [g for g in gaps if g <= 2.0]
    cv = statistics.pstdev(short) / statistics.mean(short) if len(short) >= 5 and statistics.mean(short) > 0 else 0.0
    pauses = sum(1 for g in gaps if g > 2.0)
    active_s = sum(short)
    duration = (events[-1]["t"] - events[0]["t"]) if len(events) > 1 else 0.0
    return Signals(
        typed_chars=typed, pasted_chars=pasted, deleted_chars=deleted, final_chars=final,
        paste_ratio=round(pasted / final, 3) if final else 0.0,
        revision_ratio=round(deleted / max(typed + pasted, 1), 3),
        cadence_cv=round(cv, 3),
        pause_share=round(pauses / len(gaps), 3) if gaps else 0.0,
        chars_per_active_min=round(typed / (active_s / 60), 1) if active_s else 0.0,
        duration_s=round(duration, 1),
    )


def verdict(s: Signals) -> tuple[str, list[str]]:
    reasons = []
    if s.final_chars == 0:
        return "unverified", ["no content"]
    if s.paste_ratio > 0.5:
        reasons.append(f"{s.paste_ratio:.0%} of the text was pasted in")
    if s.typed_chars >= 50 and s.cadence_cv < 0.25:
        reasons.append(f"typing rhythm is unnaturally regular (CV {s.cadence_cv})")
    if s.chars_per_active_min > 900:
        reasons.append(f"{s.chars_per_active_min:.0f} chars/min is faster than human typing")
    if reasons:
        return "unverified", reasons
    notes = []
    if s.paste_ratio > 0.1:
        notes.append(f"{s.paste_ratio:.0%} pasted (quotes, references or assisted text)")
    if s.revision_ratio < 0.02 and s.typed_chars > 500:
        notes.append("almost no revisions")
    if notes:
        return "human-led", notes
    return "human-made", [f"typed with natural rhythm (CV {s.cadence_cv}), {s.revision_ratio:.0%} revised, {s.pause_share:.0%} thinking pauses"]


def _key(key: bytes | None) -> bytes:
    return key or os.environ.get("HUMAN_MADE_KEY", "dev-key").encode()


def certify(events: list[dict], text: str, author: str, key: bytes | None = None, now: datetime | None = None) -> dict:
    s = analyze(events)
    tier, reasons = verdict(s)
    body = {
        "label": tier,
        "author": author,
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "issued_at": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
        "signals": asdict(s),
        "reasons": reasons,
        "issuer": "human-made/0.1",
    }
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return {**body, "signature": hmac.new(_key(key), payload, hashlib.sha256).hexdigest()}


def verify(cert: dict, text: str, key: bytes | None = None) -> tuple[bool, str]:
    body = {k: v for k, v in cert.items() if k != "signature"}
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    if not hmac.compare_digest(cert.get("signature", ""), hmac.new(_key(key), payload, hashlib.sha256).hexdigest()):
        return False, "signature invalid - certificate was altered or issued by someone else"
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != cert["content_sha256"]:
        return False, "text does not match the certified content"
    return True, f"{cert['label']} - {cert['author']}, {cert['issued_at']}"


def synthetic_session(text: str, human: bool = True, seed: int = 7) -> list[dict]:
    """Generate a plausible process log (for demos/tests). human=False simulates a paste."""
    import random
    rnd = random.Random(seed)
    if not human:
        return [{"t": 0.0, "type": "paste", "n": len(text), "pos": 0}]
    t, events, pos = 0.0, [], 0
    for ch in text:
        t += rnd.lognormvariate(-1.9, 0.6) + (rnd.uniform(2.5, 6) if ch in ".!?" and rnd.random() < 0.6 else 0)
        events.append({"t": round(t, 3), "type": "insert", "n": 1, "pos": pos})
        pos += 1
        if rnd.random() < 0.04:
            t += rnd.uniform(0.2, 0.6)
            events.append({"t": round(t, 3), "type": "delete", "n": 1, "pos": pos - 1})
            t += rnd.lognormvariate(-1.9, 0.5)
            events.append({"t": round(t, 3), "type": "insert", "n": 1, "pos": pos - 1})
    return events
