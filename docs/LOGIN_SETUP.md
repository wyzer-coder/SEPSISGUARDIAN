# LOGIN SETUP (Clerk + Streamlit)

SepsisGuardian uses **Streamlit's built-in login** (`st.login`) with **Clerk as the sign-in provider**
(Clerk acts as an OpenID Connect provider). Clerk shows the sign-in page and checks the password;
our app only receives the user's name and email.

**No settings → open demo.** If the `[auth]` settings are missing or incomplete, every page works without login.
**Settings present → every page shows only a "Sign in" button** until the user signs in (tested in `tests/test_app_login.py`).

## 1. In the Clerk Dashboard (your application `app_3L69QORpI46rwOecYslXY0dI9zj`)
1. Open **OAuth applications** (under Configure) → **Add OAuth application**. Menu names may differ slightly.
2. Name: `SepsisGuardian`. Scopes: `openid`, `profile`, `email`.
3. Make it a **confidential** client, so it has a **client secret**.
4. Add these **redirect URIs**:
   - `http://localhost:8501/oauth2callback` (your laptop)
   - `https://<your-app-name>.streamlit.app/oauth2callback` (after you deploy)
5. Copy the **Client ID** and **Client Secret**. Keep the secret private.
6. Find your **Frontend API URL** (shown under API keys / domains, e.g. `https://xxxx.clerk.accounts.dev`).
   Check it: open `https://<frontend-api>/.well-known/openid-configuration` in your browser.
   You should see a page of JSON text. That full address is your `server_metadata_url`.

## 2. On your laptop
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
python3 -c "import secrets; print(secrets.token_hex(32))"   # paste the result as cookie_secret
```
Open `.streamlit/secrets.toml` and fill in `client_id`, `client_secret`, `server_metadata_url` and `cookie_secret`.
Then run `.venv/bin/streamlit run app/Home.py`, click **Sign in**, and sign up or sign in on the Clerk page.
Afterwards the sidebar shows "Signed in as …" and a **Sign out** button.

`git status` must **not** list `.streamlit/secrets.toml` (it is in `.gitignore`).

## 3. On Streamlit Community Cloud
App → **Settings → Secrets**: paste the same `[auth]` block, but with
`redirect_uri = "https://<your-app-name>.streamlit.app/oauth2callback"`.

## Judges
With login on, judges must create a Clerk account before they see anything. Options:
- Give judges a test account (email + password) in your submission notes, **or**
- Leave the Cloud secrets empty for judging (open demo) and show login in the video.

## If sign-in fails
| What you see | Likely cause |
|---|---|
| Still no Sign-in button | A value in `[auth]` is empty or misspelled; all 5 are needed |
| Clerk says "redirect URI mismatch" | `redirect_uri` differs from the one listed in the Clerk OAuth app (check http vs https, the port, `/oauth2callback`) |
| Error about metadata / discovery | `server_metadata_url` is wrong; open it in a browser, it must show JSON |
| Signed in but signed out after a restart | `cookie_secret` changed; keep it the same |
| `400: 'NoneType' object does not support item assignment` | Authlib is newer than 1.6.5. Run `.venv/bin/pip install -r requirements.txt` |
| Clerk page says `invalid_client` | `client_id` / `client_secret` are wrong, or the OAuth app is not confidential |
