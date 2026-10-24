import unittest
from datetime import datetime, timezone

from human_made import analyze, certify, synthetic_session, verdict, verify

TEXT = ("I rewrote this paragraph three times before it felt right. Writing is mostly deleting, "
        "and the good sentences only show up after the bad ones get out of the way.")


class Tests(unittest.TestCase):
    def test_human_session(self):
        s = analyze(synthetic_session(TEXT))
        self.assertEqual(s.pasted_chars, 0)
        self.assertGreater(s.cadence_cv, 0.25)
        self.assertGreater(s.revision_ratio, 0)
        self.assertEqual(verdict(s)[0], "human-made")

    def test_paste_is_unverified(self):
        tier, reasons = verdict(analyze(synthetic_session(TEXT, human=False)))
        self.assertEqual(tier, "unverified")
        self.assertIn("pasted", reasons[0])

    def test_robotic_typing(self):
        events = [{"t": i * 0.1, "type": "insert", "n": 1} for i in range(200)]
        tier, reasons = verdict(analyze(events))
        self.assertEqual(tier, "unverified")
        self.assertTrue(any("regular" in r for r in reasons))

    def test_partial_paste_is_human_led(self):
        events = synthetic_session(TEXT)
        events.append({"t": events[-1]["t"] + 5, "type": "paste", "n": 40})
        self.assertEqual(verdict(analyze(events))[0], "human-led")

    def test_certificate_roundtrip_and_tamper(self):
        cert = certify(synthetic_session(TEXT), TEXT, "Sam", key=b"k", now=datetime(2026, 10, 24, tzinfo=timezone.utc))
        self.assertTrue(verify(cert, TEXT, key=b"k")[0])
        self.assertFalse(verify(cert, TEXT + "!", key=b"k")[0])
        forged = {**cert, "label": "human-made", "author": "Mallory"}
        self.assertFalse(verify(forged, TEXT, key=b"k")[0])
        self.assertFalse(verify(cert, TEXT, key=b"other")[0])


if __name__ == "__main__":
    unittest.main()
