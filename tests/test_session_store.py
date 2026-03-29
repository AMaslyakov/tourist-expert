from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.session_store import save_consultation_session


class SessionStoreTests(unittest.TestCase):
    def test_save_consultation_session_writes_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            payload = {
                "created_at_utc": "2026-03-28T00:00:00+00:00",
                "input": {"departure_city": "Екатеринбург"},
                "recommendation": "Тестовая рекомендация",
            }

            with patch("app.session_store.get_consultation_dir", return_value=temp_path):
                file_path = save_consultation_session(payload)

            self.assertTrue(file_path.exists())
            loaded = json.loads(file_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["recommendation"], "Тестовая рекомендация")
            self.assertEqual(loaded["input"]["departure_city"], "Екатеринбург")


if __name__ == "__main__":
    unittest.main()
