"""Tests for API usage tracking helpers in nori-web."""
import json
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import os
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Stub heavy imports before anything in main.py runs
import types

for mod_name in [
    "fastapi",
    "fastapi.responses",
    "fastapi.middleware",
    "fastapi.middleware.cors",
    "slowapi",
    "slowapi.errors",
    "slowapi.util",
    "pydantic",
    "requests",
    "httpx",
    "jose",
    "wynntilsresolver",
    "dotenv",
]:
    sys.modules.setdefault(mod_name, types.ModuleType(mod_name))

# Minimal stubs so module-level code in main.py doesn't crash on import
fastapi_mod = sys.modules["fastapi"]
fastapi_mod.FastAPI = lambda: MagicMock()
fastapi_mod.Request = MagicMock
fastapi_mod.HTTPException = Exception
fastapi_mod.Cookie = lambda **kw: None
fastapi_mod.Response = MagicMock

pydantic_mod = sys.modules["pydantic"]
pydantic_mod.BaseModel = object

dotenv_mod = sys.modules["dotenv"]
dotenv_mod.load_dotenv = lambda *a, **kw: None

jose_mod = sys.modules["jose"]
jose_mod.jwt = MagicMock()
jose_mod.JWTError = Exception

slowapi_mod = sys.modules["slowapi"]
slowapi_mod.Limiter = MagicMock()
slowapi_mod._rate_limit_exceeded_handler = MagicMock()
slowapi_errors = sys.modules["slowapi.errors"]
slowapi_errors.RateLimitExceeded = Exception
slowapi_util = sys.modules["slowapi.util"]
slowapi_util.get_remote_address = MagicMock()

cors_mod = sys.modules["fastapi.middleware.cors"]
cors_mod.CORSMiddleware = MagicMock

os.environ.setdefault("WYNN_API_TOKEN", "test_token")
os.environ.setdefault("SECRET_KEY", "test_secret_key")

import api_tracking  # type: ignore


TODAY = api_tracking.today_date()


class TestTodayDate(unittest.TestCase):
    def test_returns_iso_format(self):
        d = api_tracking.today_date()
        self.assertRegex(d, r"^\d{4}-\d{2}-\d{2}$")


class TestBuildFreshData(unittest.TestCase):
    def test_contains_today(self):
        route_paths = ["/api/player/{user_input}", "/api/leaderboard/raid/{raid_name}"]
        data = api_tracking.build_fresh_data(route_paths, TODAY)
        self.assertEqual(data["date"], TODAY)
        for path in route_paths:
            self.assertIn(path, data["endpoints"])
            self.assertEqual(data["endpoints"][path]["count"], 0)

    def test_includes_methods(self):
        data = api_tracking.build_fresh_data(["/api/foo"], TODAY)
        self.assertIn("methods", data["endpoints"]["/api/foo"])


class TestLoadOrReset(unittest.TestCase):
    def test_creates_fresh_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "api_usage_today.json"
            routes = ["/api/test"]
            data = api_tracking.load_or_reset(path, routes)
            self.assertEqual(data["date"], TODAY)
            self.assertIn("/api/test", data["endpoints"])

    def test_resets_when_date_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "api_usage_today.json"
            old = {"date": "1970-01-01", "updated_at": 0, "endpoints": {"/api/old": {"count": 99}}}
            path.write_text(json.dumps(old))
            routes = ["/api/new"]
            data = api_tracking.load_or_reset(path, routes)
            self.assertEqual(data["date"], TODAY)
            self.assertNotIn("/api/old", data["endpoints"])

    def test_keeps_counts_when_same_day(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "api_usage_today.json"
            existing = {
                "date": TODAY,
                "updated_at": int(time.time()),
                "endpoints": {"/api/player/{user_input}": {"count": 42, "methods": ["GET"]}},
            }
            path.write_text(json.dumps(existing))
            routes = ["/api/player/{user_input}", "/api/leaderboard"]
            data = api_tracking.load_or_reset(path, routes)
            self.assertEqual(data["endpoints"]["/api/player/{user_input}"]["count"], 42)
            # New route gets zero-initialised
            self.assertEqual(data["endpoints"]["/api/leaderboard"]["count"], 0)


class TestNormaliseRoute(unittest.TestCase):
    def test_api_path_returned_unchanged_when_template(self):
        result = api_tracking.normalise_route("/api/player/{user_input}", "/api/player/Salted")
        self.assertEqual(result, "/api/player/{user_input}")

    def test_static_api_path(self):
        result = api_tracking.normalise_route("/api/leaderboard/raid_stats", "/api/leaderboard/raid_stats")
        self.assertEqual(result, "/api/leaderboard/raid_stats")

    def test_non_api_path_returns_none(self):
        result = api_tracking.normalise_route("/wynn/leaderboard", "/wynn/leaderboard")
        self.assertIsNone(result)


class TestIncrementAndSave(unittest.TestCase):
    def test_increments_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "api_usage_today.json"
            data = {
                "date": TODAY,
                "updated_at": int(time.time()),
                "endpoints": {"/api/test": {"count": 5, "methods": ["GET"]}},
            }
            path.write_text(json.dumps(data))
            api_tracking.increment_and_save(path, "/api/test")
            result = json.loads(path.read_text())
            self.assertEqual(result["endpoints"]["/api/test"]["count"], 6)

    def test_creates_entry_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "api_usage_today.json"
            data = {
                "date": TODAY,
                "updated_at": int(time.time()),
                "endpoints": {},
            }
            path.write_text(json.dumps(data))
            api_tracking.increment_and_save(path, "/api/new_route")
            result = json.loads(path.read_text())
            self.assertEqual(result["endpoints"]["/api/new_route"]["count"], 1)


class TestFormatUsageSummary(unittest.TestCase):
    def test_basic_format(self):
        data = {
            "date": "2026-04-24",
            "updated_at": 1714000000,
            "endpoints": {
                "/api/player/{user_input}": {"count": 80, "methods": ["GET"]},
                "/api/leaderboard/raid/{raid_name}": {"count": 50, "methods": ["GET"]},
                "/api/uptime": {"count": 0, "methods": ["GET"]},
            },
        }
        text = api_tracking.format_usage_summary(data)
        self.assertIn("2026-04-24", text)
        self.assertIn("/api/player", text)
        self.assertIn("80", text)
        self.assertIn("endpoints with no traffic today", text)


if __name__ == "__main__":
    unittest.main()
