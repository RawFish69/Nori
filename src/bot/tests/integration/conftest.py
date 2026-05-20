"""Integration test fixtures.

Integration tests hit real external APIs and require network access.
Run them with: pytest -m integration
Skip them with: pytest -m "not integration"
"""
import os
import pytest

# A known stable player IGN to use across integration tests.
# Override via environment variable for CI or local customisation.
INTEGRATION_TEST_IGN = os.getenv("NORI_TEST_IGN", "Salted")
INTEGRATION_TEST_GUILD = os.getenv("NORI_TEST_GUILD", "Wynncraft")


@pytest.fixture(scope="session")
def test_ign():
    return INTEGRATION_TEST_IGN


@pytest.fixture(scope="session")
def test_guild():
    return INTEGRATION_TEST_GUILD


def pytest_collection_modifyitems(items):
    """Auto-mark any test inside tests/integration/ with the integration marker."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
