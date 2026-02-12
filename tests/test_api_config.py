import unittest

from ndefender_antsdr_scan.core.config import load_config


class ApiConfigTests(unittest.TestCase):
    def test_api_config_defaults(self) -> None:
        config = load_config("config/default.yaml")
        api = config.api
        self.assertFalse(api.enabled)
        self.assertEqual(api.bind, "127.0.0.1")
        self.assertEqual(api.port, 8890)
        self.assertEqual(api.max_clients, 25)
        self.assertEqual(api.event_buffer, 500)


if __name__ == "__main__":
    unittest.main()
