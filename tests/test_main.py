import unittest
from unittest.mock import patch

import requests

import main


class FakeResponse:
    def __init__(self, text="", status_error=None):
        self.text = text
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error is not None:
            raise self.status_error


class FakeHttpClient:
    def __init__(self, get_response=None, post_response=None):
        self.get_response = get_response or FakeResponse()
        self.post_response = post_response or FakeResponse()
        self.last_post = None

    def get(self, url, **kwargs):
        return self.get_response

    def post(self, url, **kwargs):
        self.last_post = (url, kwargs)
        return self.post_response


class SystemInfoTests(unittest.TestCase):
    def test_text_contains_only_documented_values(self):
        info = main.SystemInfo("workstation", "192.168.1.10", "203.0.113.5")

        self.assertEqual(
            info.as_text(),
            "Collection completed\n\n"
            "Hostname: workstation\n"
            "Local IP: 192.168.1.10\n"
            "Public IP: 203.0.113.5",
        )

    def test_public_ip_is_trimmed(self):
        client = FakeHttpClient(get_response=FakeResponse(" 203.0.113.5\n"))

        self.assertEqual(main.get_public_ip(client), "203.0.113.5")

    def test_public_ip_failure_is_non_fatal(self):
        error = requests.ConnectionError("offline")
        client = FakeHttpClient(get_response=FakeResponse(status_error=error))

        self.assertEqual(main.get_public_ip(client), "Unavailable")

    @patch("main.get_local_ip", return_value="192.168.1.10")
    @patch("main.socket.gethostname", return_value="workstation")
    def test_collection_happens_once(self, _hostname, _local_ip):
        client = FakeHttpClient(get_response=FakeResponse("203.0.113.5"))

        info = main.collect_system_info(client)

        self.assertEqual(
            info,
            main.SystemInfo("workstation", "192.168.1.10", "203.0.113.5"),
        )


class WebhookTests(unittest.TestCase):
    def test_valid_discord_webhook(self):
        self.assertTrue(
            main.is_valid_discord_webhook(
                "https://discord.com/api/webhooks/123456/token-value"
            )
        )

    def test_rejects_non_discord_or_incomplete_urls(self):
        invalid_urls = (
            "http://discord.com/api/webhooks/123/token",
            "https://example.com/api/webhooks/123/token",
            "https://discord.com/api/webhooks/123",
            "not-a-url",
        )

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(main.is_valid_discord_webhook(url))

    def test_send_uses_the_exact_displayed_data(self):
        client = FakeHttpClient(post_response=FakeResponse())
        info = main.SystemInfo("workstation", "192.168.1.10", "203.0.113.5")
        url = "https://discord.com/api/webhooks/123456/token-value"

        main.send_to_discord(url, info, client)

        sent_url, sent_options = client.last_post
        self.assertEqual(sent_url, url)
        self.assertEqual(
            sent_options["json"],
            {
                "content": info.as_text(),
                "allowed_mentions": {"parse": []},
            },
        )
        self.assertEqual(sent_options["timeout"], main.REQUEST_TIMEOUT_SECONDS)


if __name__ == "__main__":
    unittest.main()
