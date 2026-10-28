"""Billing shape tests: monthly checkout carries the 14-day trial, /pricing notes it."""

import pathlib
import tempfile
import threading
import unittest
import urllib.request

from human_made import web


class BillingTests(unittest.TestCase):
    def test_monthly_checkout_carries_14_day_trial(self):
        env = {
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "STRIPE_PRICES": "writer=price_123,publisher=price_456",
            "PUBLIC_URL": "https://example.test",
        }
        with tempfile.TemporaryDirectory() as t:
            srv = web.make_server("127.0.0.1", 0, pathlib.Path(t), env=env)
            billing = srv.RequestHandlerClass.billing
            sent = {}
            billing._stripe = lambda path, form: sent.update(form) or {"url": "https://checkout.test/s"}
            try:
                url = billing.checkout("writer")
                self.assertEqual(url, "https://checkout.test/s")
                self.assertEqual(sent["mode"], "subscription")
                self.assertEqual(sent["line_items[0][price]"], "price_123")
                self.assertEqual(sent["subscription_data[trial_period_days]"], "14")
            finally:
                srv.server_close()

    def test_pricing_page_notes_monthly_trial(self):
        env = {
            "STRIPE_SECRET_KEY": "sk_test_x",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "STRIPE_PRICES": "writer=price_123",
            "PUBLIC_URL": "https://example.test",
        }
        with tempfile.TemporaryDirectory() as t:
            srv = web.make_server("127.0.0.1", 0, pathlib.Path(t), env=env)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{srv.server_address[1]}"
            try:
                page = urllib.request.urlopen(base + "/pricing", timeout=30).read().decode()
                self.assertIn("14-day free trial", page)
            finally:
                srv.shutdown()
                srv.server_close()


if __name__ == "__main__":
    unittest.main()
