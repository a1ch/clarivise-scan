"""
Self-serve portal: collect signup details and issue one extension product key per submission.
Uses Supabase service role from Streamlit secrets only (server-side).
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import streamlit as st
from supabase import Client, create_client

MIN_PASSWORD_LEN = 8
SB_ACCESS = "sb_access_token"
SB_REFRESH = "sb_refresh_token"
SB_ANON = "portal_anon_client"

# Streamlit multipage paths (repo root = working directory when Cloud runs streamlit_app.py).
PAGE_STREAMLIT_HOME = "streamlit_app.py"
PAGE_REQUEST_KEY = "pages/1_Request_a_key.py"


def hash_token(plain: str) -> str:
    """SHA-256 UTF-8 digest, hex — must match supabase/functions/_shared/extension-auth.ts."""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def gen_token_plain() -> str:
    """64 hex chars (32 random bytes), same length as admin-console genToken()."""
    return secrets.token_hex(32)


def expires_at_iso(license_type: str) -> str:
    now = datetime.now(timezone.utc)
    if license_type == "annual":
        return (now + timedelta(days=365)).isoformat()
    return (now + timedelta(days=15)).isoformat()


def slugify_company(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return (s[:50] if s else "org") + "-" + secrets.token_hex(3)


_PHONE_OK = re.compile(r"^[\d\s\-+().]{7,32}$")


def validate_phone(raw: str) -> bool:
    s = (raw or "").strip()
    if len(s) < 7 or len(s) > 32:
        return False
    return bool(_PHONE_OK.match(s))


def _secret(name: str) -> str:
    """Streamlit secrets first; optional env fallback (e.g. Docker)."""
    try:
        v = st.secrets.get(name, "")
    except Exception:
        v = ""
    if v and str(v).strip():
        return str(v).strip()
    return (os.environ.get(name) or "").strip()


def _legal_doc_urls() -> tuple[str, str]:
    """Terms and Privacy URLs for the signup checkbox (secrets override defaults)."""
    terms = _secret("TERMS_URL") or "https://ingot.solutions/terms"
    privacy = (
        _secret("PRIVACY_URL")
        or "https://github.com/a1ch/outlook-email-evaluator/blob/main/PRIVACY.md"
    )
    return terms, privacy


def _portal_bootstrap() -> dict[str, str]:
    """Display names and links (optional Streamlit / env secrets)."""
    return {
        "product": _secret("PORTAL_PRODUCT_NAME") or "Outlook Email Evaluator",
        "brand": _secret("PORTAL_BRAND_NAME") or "Ingot Solutions",
        "tagline": _secret("PORTAL_TAGLINE")
        or "Real-time AI risk scores and plain-English guidance—inside Outlook on the web.",
        "repo": _secret("PORTAL_GITHUB_URL")
        or "https://github.com/a1ch/outlook-email-evaluator",
        "company_site": _secret("PORTAL_COMPANY_URL") or "https://ingot.solutions",
    }


def get_anon_client() -> Optional[Client]:
    """Supabase client with the anon (public) key — used for Auth only."""
    url = _secret("SUPABASE_URL")
    anon = _secret("SUPABASE_ANON_KEY")
    if not url or not anon:
        return None
    if SB_ANON not in st.session_state:
        st.session_state[SB_ANON] = create_client(url, anon)
    return st.session_state[SB_ANON]


def _persist_auth_session(session: Any) -> None:
    if session is None:
        return
    st.session_state[SB_ACCESS] = session.access_token
    st.session_state[SB_REFRESH] = session.refresh_token


def _clear_auth_session() -> None:
    for k in (SB_ACCESS, SB_REFRESH):
        st.session_state.pop(k, None)


def get_auth_user(client: Client) -> Optional[Any]:
    """Current Supabase Auth user, or None (invalid/expired session tokens are cleared)."""
    at = st.session_state.get(SB_ACCESS)
    rt = st.session_state.get(SB_REFRESH)
    if not at or not rt:
        return None
    try:
        client.auth.set_session(at, rt)
    except Exception:
        _clear_auth_session()
        return None
    user: Optional[Any] = None
    try:
        uresp = client.auth.get_user()
        if uresp is not None:
            user = getattr(uresp, "user", None)
    except Exception:
        pass
    if user is None:
        try:
            gs = client.auth.get_session()
            if gs is not None:
                sess = getattr(gs, "session", None) or gs
                if sess is not None:
                    user = getattr(sess, "user", None)
        except Exception:
            pass
    if user is None or not hasattr(user, "id"):
        _clear_auth_session()
        return None
    return user


def _user_email(user: Any) -> str:
    return (getattr(user, "email", None) or "").strip()


def _auth_error_message(err: Exception) -> str:
    for attr in ("message", "msg", "error_description", "name"):
        v = getattr(err, attr, None)
        if v and str(v) != type(err).__name__:
            return str(v)
    return str(err) or "Authentication failed."


def sign_out_user(client: Client) -> None:
    try:
        client.auth.sign_out()
    except Exception:
        pass
    _clear_auth_session()
    if SB_ANON in st.session_state:
        del st.session_state[SB_ANON]


def _inject_saas_theme() -> None:
    st.markdown(
        """
<style>
    :root {
      --saas-ink: #0f172a;
      --saas-muted: #64748b;
      --saas-accent: #4f46e5;
      --saas-surface: #ffffff;
      --saas-border: #e2e8f0;
    }
    .block-container { padding-top: 0.5rem !important; max-width: 1100px; }
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); }
    .saas-hero {
      background: linear-gradient(145deg, #0f172a 0%, #1e1b4b 45%, #312e81 100%);
      color: #f8fafc;
      border-radius: 20px;
      padding: 2.6rem 2.1rem 2.4rem;
      margin-bottom: 1.75rem;
      box-shadow: 0 32px 64px -24px rgba(15, 23, 42, 0.45);
      position: relative;
      overflow: hidden;
    }
    .saas-hero::after {
      content: "";
      position: absolute; top: -50%; right: -20%;
      width: 60%; height: 200%;
      background: radial-gradient(ellipse, rgba(99,102,241,0.28) 0%, transparent 70%);
      pointer-events: none;
    }
    .saas-hero-inner { position: relative; z-index: 1; }
    .saas-badge {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #c7d2fe;
      background: rgba(99, 102, 241, 0.22);
      border: 1px solid rgba(165, 180, 252, 0.35);
      border-radius: 999px;
      padding: 0.38rem 0.95rem;
      margin-bottom: 1rem;
    }
    .saas-hero h1 {
      font-size: clamp(1.65rem, 4.2vw, 2.45rem);
      font-weight: 700;
      letter-spacing: -0.03em;
      line-height: 1.12;
      margin: 0 0 0.45rem 0;
      color: #fff;
    }
    .saas-hero p.lead {
      font-size: 1.1rem;
      line-height: 1.6;
      color: #cbd5e1;
      max-width: 32rem;
      margin: 0 0 1.1rem 0;
    }
    .saas-hero .brand { color: #a5b4fc; font-size: 0.9rem; margin-top: 0.5rem; }
    .saas-hero .brand a { color: #c7d2fe !important; text-decoration: none; font-weight: 500; }
    .saas-hero .pill-row { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.6rem; }
    .saas-pill {
      font-size: 0.78rem;
      color: #e0e7ff;
      background: rgba(15, 23, 42, 0.35);
      border: 1px solid rgba(148, 163, 184, 0.2);
      border-radius: 8px;
      padding: 0.32rem 0.7rem;
    }
    .saas-trust {
      display: flex; flex-wrap: wrap; align-items: center; gap: 1.1rem 1.5rem;
      margin: 1.4rem 0 1.75rem; padding: 0 0.2rem;
      color: var(--saas-muted); font-size: 0.88rem;
    }
    .saas-trust strong { color: var(--saas-ink); }
    .saas-trust .dot { color: #cbd5e1; }
    .saas-section-title {
      font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
      text-transform: uppercase; color: var(--saas-muted);
      margin: 0 0 0.65rem 0;
    }
    .saas-h2 { font-size: 1.38rem; font-weight: 700; color: var(--saas-ink); margin: 0 0 0.9rem 0; letter-spacing: -0.02em; }
    .saas-card {
      background: var(--saas-surface);
      border: 1px solid var(--saas-border);
      border-radius: 14px;
      padding: 1.3rem 1.15rem;
      height: 100%;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    .saas-card .icon { font-size: 1.65rem; line-height: 1; margin-bottom: 0.5rem; }
    .saas-card h3 { font-size: 1.02rem; font-weight: 600; color: var(--saas-ink); margin: 0 0 0.35rem 0; }
    .saas-card p { font-size: 0.86rem; color: var(--saas-muted); line-height: 1.55; margin: 0; }
    .saas-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.85rem; }
    .saas-step {
      text-align: left; padding: 0.9rem 1rem;
      border-left: 3px solid var(--saas-accent);
      background: #f8fafc; border-radius: 0 10px 10px 0;
    }
    .saas-step .n {
      display: inline-block; min-width: 1.6rem; height: 1.6rem; line-height: 1.6rem;
      text-align: center; border-radius: 7px; background: #eef2ff; color: var(--saas-accent);
      font-weight: 700; font-size: 0.8rem; margin-bottom: 0.4rem;
    }
    .saas-step h4 { font-size: 0.9rem; font-weight: 600; margin: 0 0 0.3rem; color: var(--saas-ink); }
    .saas-step p { font-size: 0.8rem; color: var(--saas-muted); margin: 0; line-height: 1.45; }
    .saas-pricing { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.9rem; margin-bottom: 1.1rem; }
    .saas-price-card {
      border: 1px solid var(--saas-border);
      border-radius: 14px; padding: 1.4rem 1.25rem; background: #fff; position: relative;
    }
    .saas-price-card.popular { border-color: #818cf8; box-shadow: 0 0 0 1px #818cf8, 0 16px 32px -12px rgba(79, 70, 229, 0.2); }
    .saas-price-card .tag {
      position: absolute; top: -0.45rem; right: 0.9rem; background: #4f46e5;
      color: #fff; font-size: 0.62rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 6px; letter-spacing: 0.04em;
    }
    .saas-price-card h3 { margin: 0 0 0.2rem; font-size: 1.02rem; color: var(--saas-ink); }
    .saas-price-card .price { font-size: 1.35rem; font-weight: 700; color: var(--saas-ink); margin: 0.4rem 0; }
    .saas-price-card .sub { font-size: 0.78rem; color: var(--saas-muted); line-height: 1.4; }
    .saas-cta {
      background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
      border: 1px solid #c7d2fe;
      border-radius: 12px; padding: 1.05rem 1.2rem; margin: 1.25rem 0 0.5rem;
      text-align: center; font-size: 0.92rem; color: #312e81;
    }
    div[data-testid="stExpander"] details { background: #fff; border: 1px solid var(--saas-border) !important; border-radius: 10px; }
    .saas-topnav-wrap {
      background: rgba(255,255,255,0.92);
      backdrop-filter: blur(10px);
      border: 1px solid var(--saas-border);
      border-radius: 12px;
      padding: 0.35rem 0.5rem 0.5rem;
      margin-bottom: 0.75rem;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }
    .saas-topnav-title { font-size: 1.05rem; font-weight: 700; color: var(--saas-ink); line-height: 2.1rem; margin: 0; padding: 0 0.25rem; }
    .saas-topnav-links { font-size: 0.8rem; color: var(--saas-muted); line-height: 2.1rem; }
    .saas-topnav-links a { color: var(--saas-accent) !important; text-decoration: none; font-weight: 500; }
    .saas-topnav-links a:hover { text-decoration: underline; }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_portal_landing(p: dict[str, str], terms_url: str, privacy_url: str) -> None:
    """SaaS-style marketing: hero, features, how it works, pricing teaser, technical docs."""
    product, brand, tagline, repo, site = (
        p["product"],
        p["brand"],
        p["tagline"],
        p["repo"],
        p["company_site"],
    )
    st.markdown(
        f"""
<div class="saas-hero">
  <div class="saas-hero-inner">
    <div class="saas-badge">AI email defense · Microsoft 365 · Supabase-secured</div>
    <h1>{product}</h1>
    <p class="lead">{tagline}</p>
    <div class="pill-row">
      <span class="saas-pill">Claude analysis</span>
      <span class="saas-pill">No API keys in the browser</span>
      <span class="saas-pill">Works in Outlook on the web</span>
    </div>
    <p class="brand">From <a href="{site}" target="_blank" rel="noopener">{brand}</a> — ship safer email habits without another inbox to check.</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="saas-trust">
  <span><strong>Server-side</strong> — Anthropic + tokens stay in your Supabase project</span>
  <span class="dot">·</span>
  <span><strong>Team-ready</strong> — product keys for trial or annual</span>
  <span class="dot">·</span>
  <span><strong>Open</strong> — <a href="{repo}" target="_blank" rel="noopener">source on GitHub</a></span>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div style="text-align:center;font-size:0.88rem;color:#64748b;margin:0 0 1rem;padding:0.5rem 0.75rem;
  background:#f1f5f9;border-radius:10px;border:1px solid #e2e8f0;">
  <span style="font-weight:600;color:#475569;">On this page</span>
  &nbsp;·&nbsp;
  <a href="#section-product" style="color:#4f46e5;text-decoration:none;font-weight:500;">Product</a>
  &nbsp;·&nbsp;
  <a href="#section-how" style="color:#4f46e5;text-decoration:none;font-weight:500;">How it works</a>
  &nbsp;·&nbsp;
  <a href="#section-plans" style="color:#4f46e5;text-decoration:none;font-weight:500;">Plans</a>
  &nbsp;·&nbsp;
  <a href="#section-docs" style="color:#4f46e5;text-decoration:none;font-weight:500;">Docs</a>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div id="section-product" style="scroll-margin-top:6rem;"></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<p class="saas-section-title">Why teams use it</p>', unsafe_allow_html=True)
    st.markdown(f'<h2 class="saas-h2">Stop guessing in the reading pane</h2>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
<div class="saas-card">
  <div class="icon">🛡️</div>
  <h3>Phishing &amp; fraud signals</h3>
  <p>AI-assisted verdicts, risk scores, and clear explanations for suspicious senders, links, and content—right where your users already work.</p>
</div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="saas-card">
  <div class="icon">🔐</div>
  <h3>Enterprise-style trust</h3>
  <p>End users only configure a proxy URL and a product key. Your Anthropic and Supabase service credentials never ship to the desktop.</p>
</div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
<div class="saas-card">
  <div class="icon">⚡</div>
  <h3>Zero workflow swap</h3>
  <p>Chrome extension + Outlook on the web—no new app to train. Install, connect, and analyze the message in view in seconds.</p>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div id="section-how" style="scroll-margin-top:6rem;"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div style="margin: 1.5rem 0 0.75rem;">
  <p class="saas-section-title" style="margin-bottom:0.5rem">How it works</p>
  <h2 class="saas-h2" style="margin-top:0">From open email to action in three steps</h2>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div class="saas-steps">
  <div class="saas-step">
    <div class="n">1</div>
    <h4>Get a key</h4>
    <p>Click <strong>Get a product key</strong> (below), then sign in and request a <strong>trial</strong> or
    <strong>annual</strong> key for {product}.</p>
  </div>
  <div class="saas-step">
    <div class="n">2</div>
    <h4>Connect the extension</h4>
    <p>Paste your proxy URL and key under <strong>Connection</strong> in Chrome—keys never leave the secure channel you configure.</p>
  </div>
  <div class="saas-step">
    <div class="n">3</div>
    <h4>Analyze in Outlook</h4>
    <p>Open a message, hit <strong>Analyze Email</strong> in the sidebar, and use the readout to decide what to trust.</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div id="section-plans" style="scroll-margin-top:6rem;"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div style="margin: 1.5rem 0 0.75rem;">
  <p class="saas-section-title" style="margin-bottom:0.5rem">Plans</p>
  <h2 class="saas-h2" style="margin-top:0">Start fast, scale when you’re ready</h2>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="saas-pricing">
  <div class="saas-price-card">
    <h3>Trial</h3>
    <div class="price">15 days</div>
    <p class="sub">Full feature access for evaluation. Great for security pilots and team demos.</p>
  </div>
  <div class="saas-price-card popular">
    <div class="tag">Popular</div>
    <h3>Annual</h3>
    <div class="price">365 days</div>
    <p class="sub">One product key, ongoing protection in Outlook on the web—aligned to your org calendar.</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div id="section-docs" style="scroll-margin-top:6rem;"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<p class="saas-section-title" style="margin-top:1.25rem">Resources</p>
<h2 class="saas-h2" style="font-size:1.15rem">Docs &amp; operations</h2>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("What this project does", expanded=False):
        st.markdown(
            f"""
- **Who it’s for:** security-conscious teams and individuals who live in **Outlook on the web** and want a second
  opinion on **spam, phishing, and suspicious senders** before they click.
- **How it works:** a sidebar in Outlook sends **metadata and body text (length-limited)** to your
  **Supabase Edge Function**, which calls **Claude** and returns structured results to the user. The model output is
  **advisory**—users remain responsible for their own decisions.
- **Trust model:** the extension is configured with a **proxy URL** and **extension token** only; the
  **Supabase service_role** key and **Anthropic** keys stay on the server. See the
  **[Privacy Policy]({privacy_url})** and **[Terms and Conditions]({terms_url})** for what is collected and how.
- **Open source & docs:** full source and deployment instructions are in the **[GitHub repository]({repo})**.
            """.strip()
        )

    with st.expander("Set up the Chrome extension (end users)", expanded=False):
        st.markdown(
            f"""
1. Get the app from your IT team or from the **[{product}]({repo})** repo (developer / unpacked install until the
   Chrome Web Store listing is available).
2. In Chrome, open **Extensions** (e.g. `chrome://extensions`), enable **Developer mode**, **Load unpacked**, and
   select the project folder (the one that contains `manifest.json`).
3. Open the extension’s **Connection** (or **Options**) view and set:
   - **Supabase proxy URL** — your deployed function, e.g.
     `https://YOUR_PROJECT_REF.supabase.co/functions/v1/analyze-email`
   - **Extension token** — the key you receive from **this page** (or your administrator). This is *not* the
     Supabase **anon** key.
4. **Save** and use **Test connection** if the UI offers it. Open **Outlook on the web**, open a message, and use
   **Analyze Email** in the sidebar.

*Rate limits and license expiry apply to trial and annual keys; see the message shown when your key is generated.*
            """.strip()
        )

    with st.expander("Host the portal and backend (operators & IT)", expanded=False):
        st.markdown(
            f"""
**Backend (Supabase)**  
- Deploy the SQL migrations and Edge Functions in **`supabase/`** from the repo.  
- Set secrets such as **`ANTHROPIC_API_KEY`**, **`SUPABASE_URL`**, and **`SUPABASE_SERVICE_ROLE_KEY`** in the Supabase
  project. Step-by-step: **[supabase/README.md]({repo}/blob/main/supabase/README.md)** in the repository.

**This Streamlit app**  
- Recommended: **[Streamlit Community Cloud](https://streamlit.io/cloud)** with main file **`streamlit_app.py`**
  at the repo root and **Secrets** for **`SUPABASE_URL`**, **`SUPABASE_ANON_KEY`** (Auth), and **`SUPABASE_SERVICE_ROLE_KEY`**.  
- Enable **Email** sign-in under Supabase **Authentication** and set **Site URL** to your Streamlit app URL.  
- Details: **[portal/README.md]({repo}/blob/main/portal/README.md)**.  
- Use a strong optional shared passphrase via **`PORTAL_SIGNUP_SECRET`** in Streamlit secrets so the public link
  cannot be abused for unlimited keys.

**Policies**  
- **[Privacy]({privacy_url})** · **[Terms]({terms_url})**
            """.strip()
        )


def get_supabase() -> Client:
    url = _secret("SUPABASE_URL")
    key = _secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        st.error("**Supabase credentials are not configured.**")
        with st.expander("How to fix this", expanded=True):
            st.markdown(
                """
**On Streamlit Community Cloud**

1. Open your app on [share.streamlit.io](https://share.streamlit.io).
2. Click **⚙ Settings** (bottom right) → **Secrets**.
3. Paste TOML with **exact** key names (case-sensitive):

```toml
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # publishable / anon key from the same API page"
```

4. **Save** — the app will restart. Keys are in Supabase → **Project Settings → API** (use **anon** for sign-in, **service_role** for issuing keys).

**Running locally** (repo root, next to `streamlit_app.py`):

1. Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`
2. Fill in real values. Streamlit only reads **`/.streamlit/secrets.toml`** when you run from the **repository root** — not `portal/.streamlit/` unless you `cd portal` and run `app.py` there.

**Typical mistakes:** typo in key names, missing quotes around values, or secrets only added under `portal/` while Cloud runs `streamlit_app.py` from root (Cloud uses the **Secrets** UI, not files in Git).
"""
            )
        st.stop()
    return create_client(url, key)


def ensure_org(sb: Client, company: str) -> str:
    default = (st.secrets.get("DEFAULT_ORG_ID") or "").strip()
    if default:
        return default
    row = (
        sb.table("organizations")
        .insert(
            {
                "name": company.strip()[:200],
                "slug": slugify_company(company),
                "plan": "trial",
                "seat_limit": 5,
            }
        )
        .execute()
    )
    if not row.data:
        raise RuntimeError("Could not create organization.")
    return row.data[0]["id"]


def _configure_streamlit(page_key: str) -> None:
    """set_page_config once per page type per session (Streamlit allows only one per run)."""
    flag = f"_portal_st_config_{page_key}"
    if st.session_state.get(flag):
        return
    if page_key == "home":
        st.set_page_config(
            page_title="Outlook Email Evaluator — Home",
            page_icon="📧",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    else:
        st.set_page_config(
            page_title="Request a product key",
            page_icon="🔑",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    st.session_state[flag] = True


def _redirect_if_key_query_param() -> None:
    """Bookmark support: ?page=key sends users to the key request multipage script."""
    raw = st.query_params.get("page")
    if raw is None:
        return
    q = raw[0] if isinstance(raw, list) and raw else raw
    q = str(q).lower().strip()
    if q not in ("key", "request", "portal", "get-key", "get_key"):
        return
    try:
        st.switch_page(PAGE_REQUEST_KEY)
    except Exception:
        pass


def render_sidebar_navigation(
    p: dict[str, str],
    terms_url: str,
    privacy_url: str,
    repo: str,
) -> None:
    """Extra sidebar content. Streamlit already lists multipage scripts at the top of the sidebar."""
    with st.sidebar:
        st.markdown(f"### {p['product']}")
        st.caption(
            "Use the **app pages** list at the top of this sidebar to switch between the "
            "**home** entry (marketing) and **Request a key**."
        )
        st.divider()
        st.caption("Links")
        st.markdown(
            f"[GitHub]({repo}) · [Terms]({terms_url}) · [Privacy]({privacy_url})  \n"
            f"[{p['brand']}]({p['company_site']})"
        )


def render_in_page_navigation(
    p: dict[str, str],
    terms_url: str,
    privacy_url: str,
    repo: str,
) -> None:
    """Duplicate navigation in the main column so users see it even if the sidebar is collapsed."""
    st.markdown("**Navigate**")
    n1, n2, n3 = st.columns([1, 1, 2])
    with n1:
        try:
            st.page_link(PAGE_STREAMLIT_HOME, label="Home", icon="🏠", use_container_width=True)
        except TypeError:
            st.page_link(PAGE_STREAMLIT_HOME, label="Home", icon="🏠")
    with n2:
        try:
            st.page_link(PAGE_REQUEST_KEY, label="Request a key", icon="🔑", use_container_width=True)
        except TypeError:
            st.page_link(PAGE_REQUEST_KEY, label="Request a key", icon="🔑")
    with n3:
        st.markdown(
            f"[GitHub]({repo}) · [Terms]({terms_url}) · [Privacy]({privacy_url}) · "
            f"[{p['brand']}]({p['company_site']})"
        )
    st.divider()


def render_home_cta(anon: Optional[Client], p: dict[str, str]) -> None:
    st.markdown("---")
    st.markdown("### Get started")
    st.caption(
        "The next screen is for **account sign-in** and **requesting a product key**. "
        "Your work email is taken from your login."
    )
    au = get_auth_user(anon) if anon else None
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        label = "Continue to your key" if au else "Get a product key"
        if st.button(label, type="primary", use_container_width=True, key="nav_to_key_page"):
            try:
                st.switch_page(PAGE_REQUEST_KEY)
            except Exception:
                st.error("Could not open the key page. Use **Request a product key** in the sidebar.")
    if not anon:
        st.warning("Add **SUPABASE_ANON_KEY** to Streamlit secrets to enable sign-in and key requests.")
    st.caption(
        "Power users: open the key flow directly with `?page=key` in the URL (e.g. bookmark or share link)."
    )


def run_home_page() -> None:
    """Marketing homepage (streamlit_app.py)."""
    _configure_streamlit("home")
    _redirect_if_key_query_param()
    p = _portal_bootstrap()
    terms_url, privacy_url = _legal_doc_urls()
    repo = p["repo"]
    _inject_saas_theme()
    render_sidebar_navigation(p, terms_url, privacy_url, repo)
    render_in_page_navigation(p, terms_url, privacy_url, repo)
    render_portal_landing(p, terms_url, privacy_url)
    render_home_cta(get_anon_client(), p)


def run_key_request_page() -> None:
    """Sign-in and key form (pages/1_Request_a_key.py)."""
    _configure_streamlit("key")
    p = _portal_bootstrap()
    terms_url, privacy_url = _legal_doc_urls()
    repo = p["repo"]
    _inject_saas_theme()
    render_sidebar_navigation(p, terms_url, privacy_url, repo)
    render_in_page_navigation(p, terms_url, privacy_url, repo)
    st.caption(
        f"**{p['product']}** — sign in, then complete the form to generate your extension token."
    )
    st.markdown("#### Account")
    anon = get_anon_client()
    if not anon:
        st.error(
            "**SUPABASE_ANON_KEY** is missing from Streamlit secrets (or environment). "
            "Add the **anon** / **publishable** API key from Supabase → **Project Settings → API** so users can sign up and sign in."
        )
        with st.expander("Example secrets (Streamlit)", expanded=False):
            st.markdown(
                """
```toml
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_ANON_KEY = "your-anon-or-publishable-key"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"
```
"""
            )
        st.stop()

    auth_user = get_auth_user(anon)
    if auth_user:
        ac1, ac2 = st.columns([4, 1])
        with ac1:
            st.caption(f"Signed in as **{_user_email(auth_user)}**")
        with ac2:
            if st.button("Sign out", type="secondary"):
                sign_out_user(anon)
                st.rerun()
    else:
        t_reg, t_in = st.tabs(["Create account", "Sign in"])
        with t_reg:
            with st.form("register"):
                r_email = st.text_input("Email", key="reg_email_f")
                r_pw = st.text_input("Password", type="password", key="reg_pw_f", help=f"At least {MIN_PASSWORD_LEN} characters.")
                r_pw2 = st.text_input("Confirm password", type="password", key="reg_pw2_f")
                reg_btn = st.form_submit_button("Create account")
            if reg_btn:
                em = (r_email or "").strip()
                if "@" not in em or len(em) > 254:
                    st.error("Enter a valid email.")
                elif len(r_pw or "") < MIN_PASSWORD_LEN:
                    st.error(f"Password must be at least {MIN_PASSWORD_LEN} characters.")
                elif r_pw != r_pw2:
                    st.error("Passwords do not match.")
                else:
                    try:
                        res = anon.auth.sign_up({"email": em, "password": r_pw})
                        sess = getattr(res, "session", None)
                        if sess:
                            _persist_auth_session(sess)
                            st.rerun()
                        st.success(
                            "If email confirmation is enabled in Supabase, check your inbox to confirm, "
                            "then use **Sign in**. Otherwise go to **Sign in** now."
                        )
                    except Exception as ex:
                        st.error(_auth_error_message(ex))
        with t_in:
            with st.form("login"):
                l_email = st.text_input("Email", key="login_email_f")
                l_pw = st.text_input("Password", type="password", key="login_pw_f")
                login_btn = st.form_submit_button("Sign in")
            if login_btn:
                em = (l_email or "").strip()
                try:
                    res = anon.auth.sign_in_with_password({"email": em, "password": l_pw})
                    sess = getattr(res, "session", None)
                    if not sess:
                        st.error("No session returned. Confirm your email if required, or reset your password in Supabase.")
                    else:
                        _persist_auth_session(sess)
                        st.rerun()
                except Exception as ex:
                    st.error(_auth_error_message(ex))

    auth_user = get_auth_user(anon)
    if not auth_user:
        st.info("Create an account or sign in to request a **product key**.")
        st.caption("Your work email for licensing is taken from this login.")
        return

    st.divider()
    st.markdown("#### Company & key details")
    email_login = _user_email(auth_user)
    st.caption(
        f"Work email for this key: **{email_login}** (from your account). "
        "Paste the key in the extension under **Connection → Extension Token** after installing."
    )

    portal_secret = (st.secrets.get("PORTAL_SIGNUP_SECRET") or "").strip()

    with st.form("signup"):
        if portal_secret:
            invite = st.text_input(
                "Signup passphrase",
                type="password",
                help="Provided by your administrator.",
            )
        else:
            invite = ""
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("First name", placeholder="Jane")
        with c2:
            last_name = st.text_input("Last name", placeholder="Doe")
        phone = st.text_input(
            "Phone",
            placeholder="+1 555 123 4567",
            help="Include country code if outside your default region.",
        )
        company = st.text_input("Company / team name", placeholder="Acme Corp")
        st.markdown("**Mailing address**")
        address_line1 = st.text_input("Street address", placeholder="123 Main St")
        address_line2 = st.text_input(
            "Apt, suite, etc. (optional)",
            placeholder="",
        )
        ac1, ac2 = st.columns(2)
        with ac1:
            city = st.text_input("City", placeholder="Seattle")
        with ac2:
            region = st.text_input("State / province / region", placeholder="WA")
        ap1, ap2 = st.columns(2)
        with ap1:
            postal_code = st.text_input("Postal code", placeholder="98101")
        with ap2:
            country = st.text_input("Country", placeholder="United States")
        license_type = st.selectbox(
            "License",
            options=["trial", "annual"],
            format_func=lambda x: "Trial (15 days)" if x == "trial" else "Annual (365 days)",
        )
        st.markdown(
            f"Legal: [Terms and Conditions]({terms_url}) · [Privacy Policy]({privacy_url})"
        )
        agree_terms = st.checkbox(
            "I have read and agree to the Terms and Conditions and Privacy Policy.",
            value=False,
        )
        submitted = st.form_submit_button("Generate my key")

    if not submitted:
        st.caption(
            "Keys are shown **once**. Store them safely. For questions, contact your IT or security team."
        )
        return

    if portal_secret and invite != portal_secret:
        st.error("Invalid signup passphrase.")
        return

    if not agree_terms:
        st.error("You must agree to the Terms and Conditions and Privacy Policy to receive a key.")
        return

    au = get_auth_user(anon)
    if not au:
        st.error("Your session expired. Sign in again.")
        return

    email = _user_email(au)
    if not email or "@" not in email or len(email) > 254:
        st.error("Your account has no valid email. Update the user in Supabase Auth.")
        return

    company = (company or "").strip()
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    phone = (phone or "").strip()
    address_line1 = (address_line1 or "").strip()
    address_line2 = (address_line2 or "").strip()
    city = (city or "").strip()
    region = (region or "").strip()
    postal_code = (postal_code or "").strip()
    country = (country or "").strip()

    if not first_name or len(first_name) > 100:
        st.error("Please enter your first name (max 100 characters).")
        return
    if not last_name or len(last_name) > 100:
        st.error("Please enter your last name (max 100 characters).")
        return
    if not validate_phone(phone):
        st.error("Please enter a valid phone number (7–32 characters; digits and common formatting only).")
        return
    if not company or len(company) < 2:
        st.error("Please enter your company or team name.")
        return
    if not address_line1 or len(address_line1) > 200:
        st.error("Please enter a street address.")
        return
    if not city or len(city) > 100:
        st.error("Please enter a city.")
        return
    if not region or len(region) > 100:
        st.error("Please enter a state, province, or region.")
        return
    if not postal_code or len(postal_code) > 32:
        st.error("Please enter a postal code.")
        return
    if not country or len(country) > 100:
        st.error("Please enter a country.")
        return

    full_name = f"{first_name} {last_name}".strip()[:300]
    auth_uid = str(getattr(au, "id", "") or "")

    try:
        sb = get_supabase()
        org_id = ensure_org(sb, company)
        cust = (
            sb.table("customers")
            .insert(
                {
                    "org_id": org_id,
                    "email": email[:254],
                    "company_name": company[:200],
                    "full_name": full_name,
                    "first_name": first_name[:100],
                    "last_name": last_name[:100],
                    "phone": phone[:32],
                    "address_line1": address_line1[:200],
                    "address_line2": address_line2[:200] if address_line2 else None,
                    "city": city[:100],
                    "region": region[:100],
                    "postal_code": postal_code[:32],
                    "country": country[:100],
                    "signup_source": "streamlit",
                    "auth_user_id": auth_uid if auth_uid else None,
                }
            )
            .execute()
        )
        if not cust.data:
            raise RuntimeError("Could not create customer record.")
        customer_id = cust.data[0]["id"]
        plain = gen_token_plain()
        token_hash = hash_token(plain)
        exp = expires_at_iso(license_type)
        ins = (
            sb.table("extension_tokens")
            .insert(
                {
                    "token_hash": token_hash,
                    "label": company[:200],
                    "user_email": email[:254],
                    "org_id": org_id,
                    "customer_id": customer_id,
                    "license_type": license_type,
                    "expires_at": exp,
                }
            )
            .execute()
        )
        if not ins.data:
            raise RuntimeError("Insert returned no row.")
    except Exception as e:
        err = str(e).lower()
        if "unique" in err and "customers" in err:
            st.error(
                "A record for this email already exists for this organization, or you already requested a key "
                "for this login and org. Contact your administrator if you need help."
            )
        elif "duplicate key" in err or "customers_auth_user_id_org_id" in err:
            st.error(
                "You already have a signup for this organization. Contact your administrator if you need a new key."
            )
        else:
            st.error(f"Could not create key: {e}")
        return

    st.success("Your key is ready — copy it now. It cannot be shown again.")
    st.code(plain, language="text")
    st.info(
        f"**License:** {license_type} · **Valid until (UTC):** {exp}\n\n"
        "In Chrome: extension icon → **Connection** → paste the key → Save → open Outlook on the web and use **Analyze Email**."
    )


def main() -> None:
    """CLI / legacy entry: same as the Cloud main file (homepage only)."""
    run_home_page()


if __name__ == "__main__":
    main()
