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

PAGE_STREAMLIT_HOME = "streamlit_app.py"
PAGE_REQUEST_KEY    = "pages/1_Request_a_key.py"
PAGE_TERMS          = "pages/2_Terms.py"
PAGE_PRIVACY        = "pages/3_Privacy.py"


def hash_token(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()

def gen_token_plain() -> str:
    return secrets.token_hex(32)

def expires_at_iso(license_type: str) -> str:
    now = datetime.now(timezone.utc)
    return (now + timedelta(days=365 if license_type == "annual" else 15)).isoformat()

def slugify_company(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return (s[:50] if s else "org") + "-" + secrets.token_hex(3)

_PHONE_OK = re.compile(r"^[\d\s\-+().]{7,32}$")

def validate_phone(raw: str) -> bool:
    s = (raw or "").strip()
    return 7 <= len(s) <= 32 and bool(_PHONE_OK.match(s))

def _secret(name: str) -> str:
    try:
        v = st.secrets.get(name, "")
    except Exception:
        v = ""
    if v and str(v).strip():
        return str(v).strip()
    return (os.environ.get(name) or "").strip()

def _legal_doc_urls() -> tuple[str, str]:
    # Points to internal Streamlit pages — external URL only used as fallback
    return "pages/2_Terms.py", "pages/3_Privacy.py"

def _portal_bootstrap() -> dict[str, str]:
    return {
        "product": _secret("PORTAL_PRODUCT_NAME") or "Outlook Email Evaluator",
        "tagline": _secret("PORTAL_TAGLINE") or "Real-time AI risk scores and plain-English guidance—inside Outlook on the web.",
    }

def get_anon_client() -> Optional[Client]:
    url  = _secret("SUPABASE_URL")
    anon = _secret("SUPABASE_ANON_KEY")
    if not url or not anon:
        return None
    if SB_ANON not in st.session_state:
        st.session_state[SB_ANON] = create_client(url, anon)
    return st.session_state[SB_ANON]

def _persist_auth_session(session: Any) -> None:
    if session is None:
        return
    st.session_state[SB_ACCESS]  = session.access_token
    st.session_state[SB_REFRESH] = session.refresh_token

def _clear_auth_session() -> None:
    for k in (SB_ACCESS, SB_REFRESH):
        st.session_state.pop(k, None)

def get_auth_user(client: Client) -> Optional[Any]:
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
            gs   = client.auth.get_session()
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


# ── Theme ──────────────────────────────────────────────────────────────────────
def _inject_saas_theme() -> None:
    st.markdown("""
<style>
    :root { --saas-ink:#0f172a; --saas-muted:#64748b; --saas-accent:#4f46e5; --saas-surface:#fff; --saas-border:#e2e8f0; }
    .block-container { padding-top:0.5rem !important; max-width:1100px; }
    [data-testid="stAppViewContainer"] { background:linear-gradient(180deg,#f8fafc 0%,#f1f5f9 100%); }
    [data-testid="stMainBlockContainer"] { color:#1e293b; }
    section.main [data-baseweb="tab"] { color:#334155 !important; background-color:#f1f5f9 !important; }
    section.main [data-baseweb="tab"][aria-selected="true"] { color:#0f172a !important; background-color:#fff !important; border-bottom-color:#4f46e5 !important; }
    section.main [data-baseweb="input"] input,
    section.main [data-baseweb="input"] textarea { color:#0f172a !important; -webkit-text-fill-color:#0f172a !important; background-color:#fff !important; caret-color:#0f172a !important; }
    section.main label, section.main [data-testid="stWidgetLabel"] p { color:#334155 !important; }
    section.main [data-testid="stCaption"] { color:#64748b !important; }
    .saas-hero { background:linear-gradient(145deg,#0f172a 0%,#1e1b4b 45%,#312e81 100%); color:#f8fafc; border-radius:20px; padding:2.6rem 2.1rem 2.4rem; margin-bottom:1.75rem; box-shadow:0 32px 64px -24px rgba(15,23,42,.45); position:relative; overflow:hidden; }
    .saas-hero::after { content:""; position:absolute; top:-50%; right:-20%; width:60%; height:200%; background:radial-gradient(ellipse,rgba(99,102,241,.28) 0%,transparent 70%); pointer-events:none; }
    .saas-hero-inner { position:relative; z-index:1; }
    .saas-badge { display:inline-block; font-size:.72rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:#c7d2fe; background:rgba(99,102,241,.22); border:1px solid rgba(165,180,252,.35); border-radius:999px; padding:.38rem .95rem; margin-bottom:1rem; }
    .saas-hero h1 { font-size:clamp(1.65rem,4.2vw,2.45rem); font-weight:700; letter-spacing:-.03em; line-height:1.12; margin:0 0 .45rem; color:#fff; }
    .saas-hero p.lead { font-size:1.1rem; line-height:1.6; color:#cbd5e1; max-width:32rem; margin:0 0 1.1rem; }
    .saas-hero .pill-row { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:.6rem; }
    .saas-pill { font-size:.78rem; color:#e0e7ff; background:rgba(15,23,42,.35); border:1px solid rgba(148,163,184,.2); border-radius:8px; padding:.32rem .7rem; }
    .saas-trust { display:flex; flex-wrap:wrap; align-items:center; gap:1.1rem 1.5rem; margin:1.4rem 0 1.75rem; color:var(--saas-muted); font-size:.88rem; }
    .saas-trust strong { color:var(--saas-ink); }
    .saas-trust .dot { color:#cbd5e1; }
    .saas-section-title { font-size:.68rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:var(--saas-muted); margin:0 0 .65rem; }
    .saas-h2 { font-size:1.38rem; font-weight:700; color:var(--saas-ink); margin:0 0 .9rem; letter-spacing:-.02em; }
    .saas-card { background:var(--saas-surface); border:1px solid var(--saas-border); border-radius:14px; padding:1.3rem 1.15rem; height:100%; box-shadow:0 1px 2px rgba(15,23,42,.04); }
    .saas-card .icon { font-size:1.65rem; line-height:1; margin-bottom:.5rem; }
    .saas-card h3 { font-size:1.02rem; font-weight:600; color:var(--saas-ink); margin:0 0 .35rem; }
    .saas-card p { font-size:.86rem; color:var(--saas-muted); line-height:1.55; margin:0; }
    .saas-steps { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:.85rem; }
    .saas-step { text-align:left; padding:.9rem 1rem; border-left:3px solid var(--saas-accent); background:#f8fafc; border-radius:0 10px 10px 0; }
    .saas-step .n { display:inline-block; min-width:1.6rem; height:1.6rem; line-height:1.6rem; text-align:center; border-radius:7px; background:#eef2ff; color:var(--saas-accent); font-weight:700; font-size:.8rem; margin-bottom:.4rem; }
    .saas-step h4 { font-size:.9rem; font-weight:600; margin:0 0 .3rem; color:var(--saas-ink); }
    .saas-step p { font-size:.8rem; color:var(--saas-muted); margin:0; line-height:1.45; }
    .saas-pricing { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:.9rem; margin-bottom:1.1rem; }
    .saas-price-card { border:1px solid var(--saas-border); border-radius:14px; padding:1.4rem 1.25rem; background:#fff; position:relative; }
    .saas-price-card.popular { border-color:#818cf8; box-shadow:0 0 0 1px #818cf8,0 16px 32px -12px rgba(79,70,229,.2); }
    .saas-price-card .tag { position:absolute; top:-.45rem; right:.9rem; background:#4f46e5; color:#fff; font-size:.62rem; font-weight:700; padding:.2rem .5rem; border-radius:6px; letter-spacing:.04em; }
    .saas-price-card h3 { margin:0 0 .2rem; font-size:1.02rem; color:var(--saas-ink); }
    .saas-price-card .price { font-size:1.35rem; font-weight:700; color:var(--saas-ink); margin:.4rem 0; }
    .saas-price-card .sub { font-size:.78rem; color:var(--saas-muted); line-height:1.4; }
    div[data-testid="stExpander"] details { background:#fff; border:1px solid var(--saas-border) !important; border-radius:10px; }
    /* Legal page shared styles */
    .legal-container { max-width:860px; margin:0 auto; }
    .legal-hero { border-radius:16px; padding:2rem 2rem 1.75rem; margin-bottom:1.5rem; }
    .legal-hero h1 { font-size:1.6rem; font-weight:700; margin:0 0 .3rem; color:#fff; }
    .legal-hero p { font-size:.9rem; color:#94a3b8; margin:0; }
    .legal-toc { background:#f1f5f9; border:1px solid #e2e8f0; border-radius:12px; padding:1rem 1.25rem; margin-bottom:1.5rem; }
    .legal-toc p { font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:#64748b; margin:0 0 .5rem; }
    .legal-toc a { color:#4f46e5 !important; text-decoration:none; font-size:.85rem; }
    .legal-toc a:hover { text-decoration:underline; }
    .legal-section { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:1.4rem 1.5rem; margin-bottom:1rem; }
    .legal-section h2 { font-size:1rem; font-weight:700; color:#0f172a; margin:0 0 .75rem; padding-bottom:.5rem; border-bottom:1px solid #e2e8f0; }
    .legal-section p, .legal-section li { font-size:.88rem; color:#334155; line-height:1.65; }
    .legal-section ul { margin:.5rem 0 0 1rem; padding:0; }
    .legal-section li { margin-bottom:.3rem; }
    .legal-section table { width:100%; border-collapse:collapse; font-size:.82rem; margin-top:.5rem; }
    .legal-section th { background:#f1f5f9; color:#334155; font-weight:600; padding:.5rem .75rem; border:1px solid #e2e8f0; text-align:left; }
    .legal-section td { padding:.45rem .75rem; border:1px solid #e2e8f0; color:#475569; vertical-align:top; }
    .legal-warning { background:#fef3c7; border:1px solid #fbbf24; border-radius:10px; padding:1rem 1.25rem; margin-bottom:1.25rem; font-size:.85rem; color:#78350f; font-weight:500; line-height:1.55; }
    .legal-caps { font-size:.82rem; color:#475569; line-height:1.6; }
    .legal-footer { text-align:center; font-size:.78rem; color:#94a3b8; margin:1.5rem 0 .5rem; padding-top:1rem; border-top:1px solid #e2e8f0; }
</style>""", unsafe_allow_html=True)


# ── Navigation ─────────────────────────────────────────────────────────────────
def render_sidebar_navigation(p: dict[str, str]) -> None:
    with st.sidebar:
        st.markdown(f"### {p['product']}")
        st.caption("Use the pages list above to navigate.")

def render_in_page_navigation(p: dict[str, str]) -> None:
    n1, n2, n3, n4 = st.columns(4)
    with n1:
        try:
            st.page_link(PAGE_STREAMLIT_HOME, label="Home", icon="🏠", use_container_width=True)
        except TypeError:
            st.page_link(PAGE_STREAMLIT_HOME, label="Home", icon="🏠")
    with n2:
        try:
            st.page_link(PAGE_REQUEST_KEY, label="Get a Key", icon="🔑", use_container_width=True)
        except TypeError:
            st.page_link(PAGE_REQUEST_KEY, label="Get a Key", icon="🔑")
    with n3:
        try:
            st.page_link(PAGE_TERMS, label="Terms", icon="📋", use_container_width=True)
        except TypeError:
            st.page_link(PAGE_TERMS, label="Terms", icon="📋")
    with n4:
        try:
            st.page_link(PAGE_PRIVACY, label="Privacy", icon="🔒", use_container_width=True)
        except TypeError:
            st.page_link(PAGE_PRIVACY, label="Privacy", icon="🔒")
    st.divider()


# ── Home page ──────────────────────────────────────────────────────────────────
def render_portal_landing(p: dict[str, str]) -> None:
    product, tagline = p["product"], p["tagline"]
    st.markdown(f"""
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
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div class="saas-trust">
  <span><strong>Server-side</strong> — Anthropic + tokens stay in your Supabase project</span>
  <span class="dot">·</span>
  <span><strong>Team-ready</strong> — product keys for trial or annual</span>
  <span class="dot">·</span>
  <span><strong>AI-powered</strong> — real-time phishing and spam detection</span>
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div style="text-align:center;font-size:.88rem;color:#64748b;margin:0 0 1rem;padding:.5rem .75rem;background:#f1f5f9;border-radius:10px;border:1px solid #e2e8f0;">
  <span style="font-weight:600;color:#475569;">On this page</span>
  &nbsp;·&nbsp;<a href="#section-product" style="color:#4f46e5;text-decoration:none;font-weight:500;">Product</a>
  &nbsp;·&nbsp;<a href="#section-how" style="color:#4f46e5;text-decoration:none;font-weight:500;">How it works</a>
  &nbsp;·&nbsp;<a href="#section-plans" style="color:#4f46e5;text-decoration:none;font-weight:500;">Plans</a>
</div>""", unsafe_allow_html=True)

    st.markdown('<div id="section-product"></div>', unsafe_allow_html=True)
    st.markdown('<p class="saas-section-title">Why teams use it</p>', unsafe_allow_html=True)
    st.markdown('<h2 class="saas-h2">Stop guessing in the reading pane</h2>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="saas-card"><div class="icon">🛡️</div><h3>Phishing &amp; fraud signals</h3><p>AI-assisted verdicts, risk scores, and clear explanations for suspicious senders, links, and content—right where your users already work.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="saas-card"><div class="icon">🔐</div><h3>Enterprise-style trust</h3><p>End users only configure a proxy URL and a product key. Your Anthropic and Supabase credentials never ship to the desktop.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="saas-card"><div class="icon">⚡</div><h3>Zero workflow swap</h3><p>Chrome extension + Outlook on the web—no new app to train. Install, connect, and analyze the message in view in seconds.</p></div>', unsafe_allow_html=True)

    st.markdown('<div id="section-how"></div>', unsafe_allow_html=True)
    st.markdown('<div style="margin:1.5rem 0 .75rem;"><p class="saas-section-title">How it works</p><h2 class="saas-h2" style="margin-top:0">From open email to action in three steps</h2></div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="saas-steps">
  <div class="saas-step"><div class="n">1</div><h4>Get a key</h4><p>Sign in above and request a <strong>trial</strong> or <strong>annual</strong> key for {product}.</p></div>
  <div class="saas-step"><div class="n">2</div><h4>Connect the extension</h4><p>Paste your proxy URL and key under <strong>Connection</strong> in Chrome.</p></div>
  <div class="saas-step"><div class="n">3</div><h4>Analyze in Outlook</h4><p>Open a message, hit <strong>Analyze Email</strong> in the sidebar, and use the readout to decide what to trust.</p></div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div id="section-plans"></div>', unsafe_allow_html=True)
    st.markdown('<div style="margin:1.5rem 0 .75rem;"><p class="saas-section-title">Plans</p><h2 class="saas-h2" style="margin-top:0">Start fast, scale when you\'re ready</h2></div>', unsafe_allow_html=True)
    st.markdown("""
<div class="saas-pricing">
  <div class="saas-price-card"><h3>Trial</h3><div class="price">15 days</div><p class="sub">Full feature access for evaluation. Great for security pilots and team demos.</p></div>
  <div class="saas-price-card popular"><div class="tag">Popular</div><h3>Annual</h3><div class="price">365 days</div><p class="sub">One product key, ongoing protection in Outlook on the web—aligned to your org calendar.</p></div>
</div>""", unsafe_allow_html=True)

    with st.expander("What this product does", expanded=False):
        st.markdown("""
- **Who it's for:** security-conscious teams and individuals who live in **Outlook on the web** and want a second opinion on **spam, phishing, and suspicious senders** before they click.
- **How it works:** a sidebar in Outlook sends **metadata and body text (length-limited)** to a secure **Supabase Edge Function**, which calls **Claude AI** and returns structured results to the user.
- **Trust model:** the extension is configured with a **proxy URL** and **extension token** only; Supabase service and Anthropic keys stay on the server.
        """.strip())

    with st.expander("Set up the Chrome extension", expanded=False):
        st.markdown("""
1. Install the extension from your IT team or load it unpacked from the source folder containing `manifest.json`.
2. In Chrome open **Extensions**, enable **Developer mode**, click **Load unpacked**, select the folder.
3. In the extension popup set your **Supabase proxy URL** and **Extension token** under the **Connection** tab.
4. Open **Outlook on the web**, open a message, and click **Analyze Email** in the sidebar.
        """.strip())


def render_home_cta(anon: Optional[Client], p: dict[str, str]) -> None:
    st.markdown("---")
    st.markdown("### Get started")
    st.caption("Sign in and request a product key to activate the extension.")
    au = get_auth_user(anon) if anon else None
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        label = "Continue to your key" if au else "Get a product key"
        if st.button(label, type="primary", use_container_width=True, key="nav_to_key_page"):
            try:
                st.switch_page(PAGE_REQUEST_KEY)
            except Exception:
                st.error("Use **Get a Key** in the navigation above.")
    if not anon:
        st.warning("Add **SUPABASE_ANON_KEY** to Streamlit secrets to enable sign-in.")


# ── Terms page ─────────────────────────────────────────────────────────────────
def render_terms_content() -> None:
    st.markdown("""
<div class="legal-container">
<div class="legal-hero" style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);">
  <h1>📋 Terms and Conditions of Use</h1>
  <p>Outlook Email Evaluator &nbsp;·&nbsp; Effective: April 4, 2026 &nbsp;·&nbsp; Governing jurisdiction: Province of Alberta, Canada</p>
</div>
<div class="legal-warning">
  ⚠️ <strong>IMPORTANT:</strong> BY INSTALLING OR USING THE SOFTWARE, OR BY SUBMITTING INFORMATION THROUGH THE SIGNUP PORTAL, YOU AGREE TO THESE TERMS. IF YOU DO NOT AGREE, DO NOT USE THE SOFTWARE OR THE PORTAL.
</div>
<div class="legal-toc">
  <p>Contents</p>
  <a href="#s1">1. Definitions</a> &nbsp;·&nbsp; <a href="#s2">2. Acceptance</a> &nbsp;·&nbsp; <a href="#s3">3. Nature of the Service</a> &nbsp;·&nbsp; <a href="#s4">4. Disclaimer of Warranties</a> &nbsp;·&nbsp; <a href="#s5">5. Limitation of Liability</a> &nbsp;·&nbsp; <a href="#s6">6. Indemnity</a> &nbsp;·&nbsp; <a href="#s7">7. License and Restrictions</a> &nbsp;·&nbsp; <a href="#s8">8. Signup Portal and Account Data</a> &nbsp;·&nbsp; <a href="#s9">9. Third-Party Services</a> &nbsp;·&nbsp; <a href="#s10">10. Privacy</a> &nbsp;·&nbsp; <a href="#s11">11. Intellectual Property</a> &nbsp;·&nbsp; <a href="#s12">12. Suspension and Termination</a> &nbsp;·&nbsp; <a href="#s13">13. Changes</a> &nbsp;·&nbsp; <a href="#s14">14. Governing Law</a> &nbsp;·&nbsp; <a href="#s15">15. General</a> &nbsp;·&nbsp; <a href="#s16">16. Contact</a>
</div>
<div class="legal-section" id="s1"><h2>1. Definitions</h2><ul>
  <li><strong>"Software"</strong> means the Outlook Email Evaluator browser extension, related documentation, and any product key or signup portal operated by or on behalf of Ingot Solutions.</li>
  <li><strong>"Ingot Solutions," "we," "us"</strong> means Ingot Solutions (operating entity as identified on ingot.solutions).</li>
  <li><strong>"You," "your"</strong> means the individual or organization using the Software or portal.</li>
</ul></div>
<div class="legal-section" id="s2"><h2>2. Acceptance</h2><p>By installing, accessing, or using the Software, or by submitting a signup form to obtain a product key, you confirm that you have read these Terms, that you are authorized to bind yourself (and, if applicable, your employer) to them, and that you agree to be bound.</p></div>
<div class="legal-section" id="s3"><h2>3. Nature of the Service (AI Analysis)</h2><p>The Software uses artificial intelligence to suggest whether an email may be spam, phishing, or otherwise suspicious. Outputs are <strong>probabilistic</strong> and may be <strong>wrong</strong>. The Software is a <strong>supplement</strong> to—not a replacement for—your own judgment, security tooling, policies, and training. <strong>You remain solely responsible</strong> for decisions you make about emails, links, attachments, and data handling.</p></div>
<div class="legal-section" id="s4"><h2>4. Disclaimer of Warranties</h2><p class="legal-caps">TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE." INGOT SOLUTIONS DISCLAIMS ALL WARRANTIES, WHETHER EXPRESS, IMPLIED, OR STATUTORY, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT. WE DO NOT WARRANT THAT THE SOFTWARE WILL BE ERROR-FREE, UNINTERRUPTED, OR FREE OF HARMFUL COMPONENTS.</p></div>
<div class="legal-section" id="s5"><h2>5. Limitation of Liability</h2>
  <p class="legal-caps">TO THE MAXIMUM EXTENT PERMITTED BY LAW, IN NO EVENT SHALL INGOT SOLUTIONS BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS, DATA, GOODWILL, OR BUSINESS, ARISING OUT OF OR RELATED TO THESE TERMS OR THE SOFTWARE.</p>
  <p class="legal-caps" style="margin-top:.75rem;">INGOT SOLUTIONS' TOTAL AGGREGATE LIABILITY SHALL NOT EXCEED THE GREATER OF (A) AMOUNTS YOU PAID IN THE TWELVE (12) MONTHS BEFORE THE CLAIM, OR (B) ONE HUNDRED CANADIAN DOLLARS (CAD $100) IF NO FEES APPLIED.</p>
  <p style="margin-top:.75rem;"><strong>Email misclassification:</strong> You expressly acknowledge that Ingot Solutions shall not be liable for any loss or damage resulting from incorrect classification of email, including security incidents, financial loss, or regulatory exposure.</p>
</div>
<div class="legal-section" id="s6"><h2>6. Indemnity</h2><p>You will defend, indemnify, and hold harmless Ingot Solutions and its officers, directors, employees, and agents from and against any claims, damages, losses, liabilities, costs, and expenses (including reasonable legal fees) arising out of or related to: (a) your use of the Software; (b) your violation of these Terms; (c) your violation of any law or third-party right; or (d) data you submit through the Software or signup portal.</p></div>
<div class="legal-section" id="s7"><h2>7. License and Restrictions</h2><p>Subject to these Terms, Ingot Solutions grants you a limited, non-exclusive, non-transferable, revocable license to use the Software. You may not reverse engineer, resell, sublicense, or use the Software to build a competing product. Product keys are for your internal use only.</p></div>
<div class="legal-section" id="s8"><h2>8. Signup Portal and Account Data</h2><p>If you request a product key through the signup portal, you may be asked to provide <strong>name, work email, phone number, company name, and mailing address.</strong> That information is used to fulfill your request, operate licensing, and communicate with you. It is not sold. You represent that information you submit is accurate.</p></div>
<div class="legal-section" id="s9"><h2>9. Third-Party Services</h2><p>The Software relies on infrastructure and AI providers including Supabase and Anthropic. Your use is also subject to their applicable terms and policies.</p></div>
<div class="legal-section" id="s10"><h2>10. Privacy</h2><p>Personal data collected through the extension and related services is described in our <strong>Privacy Policy</strong> (see the Privacy page in this portal). The Privacy Policy prevails over these Terms for privacy matters.</p></div>
<div class="legal-section" id="s11"><h2>11. Intellectual Property</h2><p>The Software, branding, and documentation are owned by Ingot Solutions or its licensors. Except for the limited license above, no rights are granted.</p></div>
<div class="legal-section" id="s12"><h2>12. Suspension and Termination</h2><p>We may suspend or terminate access if you breach these Terms, if required by law, or to protect security. You may stop using the Software at any time. Provisions that by nature should survive termination (disclaimers, liability limits, indemnity) do survive.</p></div>
<div class="legal-section" id="s13"><h2>13. Changes to These Terms</h2><p>We may update these Terms by posting a revised version. The effective date will be updated. Continued use after changes constitutes acceptance.</p></div>
<div class="legal-section" id="s14"><h2>14. Governing Law and Venue</h2><p>These Terms are governed by the laws of the <strong>Province of Alberta</strong> and the federal laws of <strong>Canada</strong>. You attorn to the exclusive jurisdiction of the courts located in Alberta, subject to mandatory consumer protections where you reside.</p></div>
<div class="legal-section" id="s15"><h2>15. General</h2><p>If any provision is unenforceable, the remainder remains in effect. Failure to enforce a provision is not a waiver. These Terms constitute the entire agreement regarding the Software.</p></div>
<div class="legal-section" id="s16"><h2>16. Contact</h2><p>For questions about these Terms, contact Ingot Solutions through the channels listed at ingot.solutions or as provided with your order or support agreement.</p></div>
<div class="legal-footer">© 2026 Ingot Solutions. All rights reserved. &nbsp;·&nbsp; Version 1.1</div>
</div>""", unsafe_allow_html=True)


# ── Privacy page ───────────────────────────────────────────────────────────────
def render_privacy_content() -> None:
    st.markdown("""
<div class="legal-container">
<div class="legal-hero" style="background:linear-gradient(135deg,#0f172a 0%,#1a4731 100%);">
  <h1>🔒 Privacy Policy</h1>
  <p>Outlook Email Evaluator &nbsp;·&nbsp; Last updated: March 27, 2026</p>
</div>
<div class="legal-section"><h2>Overview</h2><p>Outlook Email Evaluator is a Chrome extension that analyzes emails in Microsoft Outlook Web for spam and phishing threats using AI. This policy explains what data is collected, how it flows, and how it is protected.</p></div>

<div class="legal-section"><h2>Product Key Signup Portal</h2><p>If you request an extension product key through the signup portal, you may be asked to <strong>create a login</strong> (email and password) via Supabase Auth, then provide <strong>first name, last name, phone number, company or team name, and mailing address.</strong></p>
<p style="margin-top:.6rem;">That information is stored in the operator's Supabase project and used to <strong>issue and manage keys</strong>, <strong>operate the service</strong>, and <strong>contact you</strong> if needed. It is <strong>not sold</strong>. Access is restricted to service administrators.</p></div>

<div class="legal-section"><h2>Architecture</h2><p>This extension does not call AI services directly from your browser. Instead, it sends email metadata to a secure proxy service hosted on Supabase, which forwards the request to the Anthropic Claude API. Your Anthropic API key is stored on the server and never touches your browser.</p></div>

<div class="legal-section"><h2>Data Collected</h2><p>When you click <strong>Analyze Email</strong>, the following is extracted from the open email and sent to the proxy service:</p>
<ul>
  <li>Email subject line</li>
  <li>Sender display name</li>
  <li>Recipient / To line (when visible)</li>
  <li>Email body text (up to 3,000 characters)</li>
  <li>Hyperlink display text and destination domains from the email body</li>
  <li>Attachment file names (if present)</li>
  <li>Whether Outlook flagged the sender as external</li>
  <li>Optional: your organization domain and any additional instructions you saved in the extension</li>
</ul>
<p style="margin-top:.6rem;">No email content beyond these fields is collected or transmitted.</p></div>

<div class="legal-section"><h2>Data Flow</h2>
<table>
  <tr><th>Step</th><th>What happens</th><th>Who can see email content?</th></tr>
  <tr><td>1. Your browser</td><td>Extension reads the email from the Outlook page</td><td>You (local only)</td></tr>
  <tr><td>2. Network transit</td><td>Data sent over HTTPS (TLS encrypted)</td><td>No one (encrypted)</td></tr>
  <tr><td>3. Supabase Edge Function</td><td>Validates token, builds AI prompt, forwards to Anthropic</td><td>In memory only — not logged or stored by Supabase</td></tr>
  <tr><td>4. Anthropic API</td><td>Analyzes the email and returns a verdict</td><td>Anthropic (see below)</td></tr>
  <tr><td>5. Response</td><td>Result returned to your browser and displayed in the sidebar</td><td>You (local only)</td></tr>
</table>
<p style="margin-top:.6rem;">Email content is processed transiently for inference. Full message bodies are <strong>not</strong> stored in the database.</p></div>

<div class="legal-section"><h2>Anthropic API</h2><p>This extension uses the Anthropic Claude API for email analysis. Per Anthropic's API data policy:</p>
<ul>
  <li>API inputs are <strong>not used for model training</strong> by default.</li>
  <li>API data may be <strong>retained for up to 30 days</strong> for trust and safety purposes, then deleted.</li>
  <li>Anthropic employees may access data during that period for safety review.</li>
</ul>
<p style="margin-top:.6rem;">Your use is subject to Anthropic's Privacy Policy and Terms of Service.</p></div>

<div class="legal-section"><h2>Supabase</h2><p>The proxy service runs as a Supabase Edge Function. Supabase acts as a <strong>data processor</strong> under their Data Processing Addendum. Supabase does not inspect, store, or share the email content that passes through the function. Infrastructure is hosted on AWS.</p></div>

<div class="legal-section"><h2>Scan Logging</h2><p>Each analysis logs the following to a Supabase database for usage reporting and troubleshooting:</p>
<ul>
  <li>A <strong>hashed</strong> identifier for the extension token (not the token itself)</li>
  <li>Verdict (Safe / Suspicious / Spam / Phishing)</li>
  <li>Phishing risk score and spam score</li>
  <li>Response time and timestamp</li>
  <li>Subject line, From, and To — <strong>truncated lengths only</strong></li>
</ul>
<p style="margin-top:.6rem;"><strong>Message body text is not written to the scan log.</strong></p></div>

<div class="legal-section"><h2>Local Storage</h2><p>The following are stored locally in your browser using Chrome's <code>chrome.storage.local</code> API and never leave your device except as described above:</p>
<ul>
  <li><strong>Proxy URL</strong> — the address of the Supabase Edge Function</li>
  <li><strong>Extension token</strong> — authenticates your requests to the proxy</li>
  <li><strong>Organization domain</strong> — used to detect external senders</li>
  <li><strong>Custom instructions</strong> — optional text passed to the AI on each analysis</li>
</ul></div>

<div class="legal-section"><h2>Permissions Used</h2><ul>
  <li><strong>activeTab</strong> — to read the content of the Outlook tab you are currently viewing</li>
  <li><strong>storage</strong> — to store your settings locally in your browser</li>
  <li><strong>Host permission for outlook.cloud.microsoft, outlook.office.com, outlook.office365.com</strong> — to inject the sidebar UI into Outlook Web</li>
  <li><strong>Host permission for *.supabase.co</strong> — to send analysis requests to the proxy service</li>
</ul></div>

<div class="legal-section"><h2>Data Sharing</h2><p>This extension does not sell, share, or disclose any user data to any third party. Email data is transmitted only to:</p>
<ul>
  <li><strong>Supabase</strong> (infrastructure provider, data processor) — transiently, during Edge Function execution</li>
  <li><strong>Anthropic</strong> (AI provider) — for email analysis, subject to their data retention policy</li>
</ul>
<p style="margin-top:.6rem;">No other parties receive any data.</p></div>

<div class="legal-section"><h2>Children's Privacy</h2><p>This extension is not directed at children under the age of 13 and does not knowingly collect data from children.</p></div>

<div class="legal-section"><h2>Changes to This Policy</h2><p>This privacy policy may be updated periodically. The date at the top of this document reflects the most recent revision. Continued use of the extension after changes constitutes acceptance of the updated policy.</p></div>

<div class="legal-section"><h2>Contact</h2><p>For questions about this privacy policy, contact Ingot Solutions through the channels listed at ingot.solutions or through the support channels provided with your license.</p></div>

<div class="legal-footer">© 2026 Ingot Solutions. All rights reserved.</div>
</div>""", unsafe_allow_html=True)


# ── Supabase helpers ────────────────────────────────────────────────────────────
def get_supabase() -> Client:
    url = _secret("SUPABASE_URL")
    key = _secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        st.error("**Supabase credentials are not configured.**")
        st.stop()
    return create_client(url, key)

def ensure_org(sb: Client, company: str) -> str:
    default = (st.secrets.get("DEFAULT_ORG_ID") or "").strip()
    if default:
        return default
    row = sb.table("organizations").insert({"name": company.strip()[:200], "slug": slugify_company(company), "plan": "trial", "seat_limit": 5}).execute()
    if not row.data:
        raise RuntimeError("Could not create organization.")
    return row.data[0]["id"]


# ── Page config ─────────────────────────────────────────────────────────────────
def _configure_streamlit(page_key: str) -> None:
    flag = f"_portal_st_config_{page_key}"
    if st.session_state.get(flag):
        return
    configs = {
        "home":    ("Outlook Email Evaluator", "📧"),
        "key":     ("Request a Product Key", "🔑"),
        "terms":   ("Terms and Conditions", "📋"),
        "privacy": ("Privacy Policy", "🔒"),
    }
    title, icon = configs.get(page_key, ("Outlook Email Evaluator", "📧"))
    st.set_page_config(page_title=title, page_icon=icon, layout="wide", initial_sidebar_state="expanded")
    st.session_state[flag] = True

def _redirect_if_query_param() -> None:
    raw = st.query_params.get("page")
    if raw is None:
        return
    q = str(raw[0] if isinstance(raw, list) and raw else raw).lower().strip()
    dest = {
        "key": PAGE_REQUEST_KEY, "request": PAGE_REQUEST_KEY, "get-key": PAGE_REQUEST_KEY,
        "terms": PAGE_TERMS, "tos": PAGE_TERMS, "legal": PAGE_TERMS,
        "privacy": PAGE_PRIVACY, "policy": PAGE_PRIVACY,
    }.get(q)
    if dest:
        try:
            st.switch_page(dest)
        except Exception:
            pass


# ── Key request form ────────────────────────────────────────────────────────────
def _render_key_request_form(anon: Client, p: dict[str, str]) -> None:
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
                r_pw    = st.text_input("Password", type="password", key="reg_pw_f", help=f"At least {MIN_PASSWORD_LEN} characters.")
                r_pw2   = st.text_input("Confirm password", type="password", key="reg_pw2_f")
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
                        st.success("Check your inbox to confirm your email, then use **Sign in**.")
                    except Exception as ex:
                        st.error(_auth_error_message(ex))
        with t_in:
            with st.form("login"):
                l_email   = st.text_input("Email", key="login_email_f")
                l_pw      = st.text_input("Password", type="password", key="login_pw_f")
                login_btn = st.form_submit_button("Sign in")
            if login_btn:
                try:
                    res = anon.auth.sign_in_with_password({"email": (l_email or "").strip(), "password": l_pw})
                    sess = getattr(res, "session", None)
                    if not sess:
                        st.error("No session returned. Confirm your email or reset your password.")
                    else:
                        _persist_auth_session(sess)
                        st.rerun()
                except Exception as ex:
                    st.error(_auth_error_message(ex))

    auth_user = get_auth_user(anon)
    if not auth_user:
        st.info("Create an account or sign in to request a **product key**.")
        return

    st.divider()
    st.markdown("#### Company & key details")
    email_login = _user_email(auth_user)
    st.caption(f"Work email for this key: **{email_login}**. Paste the key in the extension under **Connection → Extension Token** after installing.")

    portal_secret = (st.secrets.get("PORTAL_SIGNUP_SECRET") or "").strip()
    terms_url, privacy_url = _legal_doc_urls()

    with st.form("signup"):
        if portal_secret:
            invite = st.text_input("Signup passphrase", type="password", help="Provided by your administrator.")
        else:
            invite = ""
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("First name", placeholder="Jane")
        with c2:
            last_name = st.text_input("Last name", placeholder="Doe")
        phone   = st.text_input("Phone", placeholder="+1 555 123 4567")
        company = st.text_input("Company / team name", placeholder="Acme Corp")
        st.markdown("**Mailing address**")
        address_line1 = st.text_input("Street address", placeholder="123 Main St")
        address_line2 = st.text_input("Apt, suite, etc. (optional)")
        ac1, ac2 = st.columns(2)
        with ac1:
            city = st.text_input("City", placeholder="Calgary")
        with ac2:
            region = st.text_input("State / province / region", placeholder="AB")
        ap1, ap2 = st.columns(2)
        with ap1:
            postal_code = st.text_input("Postal code", placeholder="T2P 0A1")
        with ap2:
            country = st.text_input("Country", placeholder="Canada")
        license_type = st.selectbox("License", options=["trial", "annual"], format_func=lambda x: "Trial (15 days)" if x == "trial" else "Annual (365 days)")
        st.markdown("Legal: [Terms and Conditions](pages/2_Terms.py) · [Privacy Policy](pages/3_Privacy.py)")
        agree_terms = st.checkbox("I have read and agree to the Terms and Conditions and Privacy Policy.", value=False)
        submitted = st.form_submit_button("Generate my key")

    if not submitted:
        st.caption("Keys are shown **once**. Store them safely.")
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

    email         = _user_email(au)
    first_name    = (first_name or "").strip()
    last_name     = (last_name or "").strip()
    phone         = (phone or "").strip()
    company       = (company or "").strip()
    address_line1 = (address_line1 or "").strip()
    address_line2 = (address_line2 or "").strip()
    city          = (city or "").strip()
    region        = (region or "").strip()
    postal_code   = (postal_code or "").strip()
    country       = (country or "").strip()

    if not first_name:  st.error("Please enter your first name."); return
    if not last_name:   st.error("Please enter your last name."); return
    if not validate_phone(phone): st.error("Please enter a valid phone number."); return
    if not company or len(company) < 2: st.error("Please enter your company or team name."); return
    if not address_line1: st.error("Please enter a street address."); return
    if not city:          st.error("Please enter a city."); return
    if not region:        st.error("Please enter a state, province, or region."); return
    if not postal_code:   st.error("Please enter a postal code."); return
    if not country:       st.error("Please enter a country."); return

    try:
        sb        = get_supabase()
        org_id    = ensure_org(sb, company)
        full_name = f"{first_name} {last_name}".strip()[:300]
        auth_uid  = str(getattr(au, "id", "") or "")
        cust = sb.table("customers").insert({
            "org_id": org_id, "email": email[:254], "company_name": company[:200],
            "full_name": full_name, "first_name": first_name[:100], "last_name": last_name[:100],
            "phone": phone[:32], "address_line1": address_line1[:200],
            "address_line2": address_line2[:200] if address_line2 else None,
            "city": city[:100], "region": region[:100], "postal_code": postal_code[:32],
            "country": country[:100], "signup_source": "streamlit",
            "auth_user_id": auth_uid if auth_uid else None,
        }).execute()
        if not cust.data:
            raise RuntimeError("Could not create customer record.")
        plain      = gen_token_plain()
        token_hash = hash_token(plain)
        exp        = expires_at_iso(license_type)
        ins = sb.table("extension_tokens").insert({
            "token_hash": token_hash, "label": company[:200], "user_email": email[:254],
            "org_id": org_id, "customer_id": cust.data[0]["id"],
            "license_type": license_type, "expires_at": exp,
        }).execute()
        if not ins.data:
            raise RuntimeError("Insert returned no row.")
    except Exception as e:
        err = str(e).lower()
        if "unique" in err and "customers" in err:
            st.error("A record for this email already exists. Contact your administrator if you need a new key.")
        else:
            st.error(f"Could not create key: {e}")
        return

    st.success("Your key is ready — copy it now. It cannot be shown again.")
    st.code(plain, language="text")
    st.info(
        f"**License:** {license_type} · **Valid until (UTC):** {exp}\n\n"
        "In Chrome: extension icon → **Connection** → paste the key → Save → open Outlook on the web and use **Analyze Email**."
    )


# ── Page entry points ───────────────────────────────────────────────────────────
def run_home_page() -> None:
    _configure_streamlit("home")
    _redirect_if_query_param()
    p = _portal_bootstrap()
    _inject_saas_theme()
    render_sidebar_navigation(p)
    render_in_page_navigation(p)
    render_portal_landing(p)
    render_home_cta(get_anon_client(), p)

def run_terms_page() -> None:
    _configure_streamlit("terms")
    p = _portal_bootstrap()
    _inject_saas_theme()
    render_sidebar_navigation(p)
    render_in_page_navigation(p)
    render_terms_content()

def run_privacy_page() -> None:
    _configure_streamlit("privacy")
    p = _portal_bootstrap()
    _inject_saas_theme()
    render_sidebar_navigation(p)
    render_in_page_navigation(p)
    render_privacy_content()

def run_key_request_page() -> None:
    _configure_streamlit("key")
    p = _portal_bootstrap()
    _inject_saas_theme()
    render_sidebar_navigation(p)
    render_in_page_navigation(p)
    st.caption(f"**{p['product']}** — sign in, then complete the form to generate your extension token.")
    st.markdown("#### Account")
    anon = get_anon_client()
    if not anon:
        st.error("**SUPABASE_ANON_KEY** is missing from Streamlit secrets.")
        st.stop()
    _render_key_request_form(anon, p)

def main() -> None:
    run_home_page()

if __name__ == "__main__":
    main()
