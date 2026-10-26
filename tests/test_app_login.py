"""The website opens without login settings, and hides everything behind sign-in when login is configured."""

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))  # the pages import utils.py from app/

PAGES = ["Home.py", "pages/1_Ward_Overview.py", "pages/2_Patient_Detail.py", "pages/3_Results.py"]
FAKE_AUTH = {
    "redirect_uri": "http://localhost:8501/oauth2callback",
    "cookie_secret": "test-cookie-secret",
    "client_id": "test-client-id",
    "client_secret": "test-client-secret",
    "server_metadata_url": "https://example.clerk.accounts.dev/.well-known/openid-configuration",
}


def run_page(page: str, auth=None) -> AppTest:
    """Run one page headless, optionally with login settings."""
    app = AppTest.from_file(str(APP_DIR / page), default_timeout=60)
    if auth is not None:
        app.secrets["auth"] = auth
    app.run()
    return app


def page_text(app: AppTest) -> str:
    """All titles and markdown text on the page, joined together."""
    parts = [element.value for element in app.title] + [element.value for element in app.markdown]
    return "\n".join(str(part) for part in parts)


def test_pages_open_without_login_settings():
    for page in PAGES:
        app = run_page(page)
        assert not app.exception, f"{page}: {app.exception}"
        assert "Sign in" not in [button.label for button in app.button]


def test_pages_show_only_sign_in_when_login_is_configured():
    for page in PAGES:
        app = run_page(page, auth=FAKE_AUTH)
        assert not app.exception, f"{page}: {app.exception}"
        assert [button.label for button in app.button] == ["Sign in"]
        assert "Please sign in" in page_text(app)
        assert "Beds at ICU hour" not in page_text(app)       # ward data hidden
        assert len(app.dataframe) == 0 and len(app.table) == 0  # no patient tables


def test_incomplete_login_settings_keep_the_open_demo():
    partial = dict(FAKE_AUTH)
    del partial["client_secret"]
    app = run_page("Home.py", auth=partial)
    assert not app.exception
    assert "Sign in" not in [button.label for button in app.button]


def test_installed_authlib_works_with_streamlit_sign_in():
    """Streamlit keeps the sign-in state in a cache and passes no session.

    Authlib 1.6.6+ still writes into that missing session and sign-in fails with
    "'NoneType' object does not support item assignment". This catches an accidental upgrade.
    """
    from authlib.integrations.base_client.framework_integration import FrameworkIntegration

    class MemoryCache:
        def __init__(self):
            self.store = {}

        def get(self, key):
            return self.store.get(key)

        def set(self, key, value, expires=None):
            self.store[key] = value

        def delete(self, key):
            self.store.pop(key, None)

    integration = FrameworkIntegration("default", cache=MemoryCache())
    integration.set_state_data(None, "state123", {"redirect_uri": "http://localhost:8501/oauth2callback"})
    assert integration.get_state_data(None, "state123") == {"redirect_uri": "http://localhost:8501/oauth2callback"}
    integration.clear_state_data(None, "state123")
    assert integration.get_state_data(None, "state123") is None
