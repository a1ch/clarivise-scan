"""
Clarivise — Download Documentation

Streamlit page for users to download guides and manuals after signup.
"""

import streamlit as st
from pathlib import Path

def _configure_streamlit():
    st.set_page_config(
        page_title="Download Guides — Clarivise",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

def _inject_theme():
    st.markdown("""
<style>
    :root { --accent: #4f46e5; --surface: #fff; --border: #e2e8f0; }
    .block-container { max-width: 900px; }
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); }
    .guide-card { border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; background: white; margin: 1rem 0; }
    .guide-card h3 { color: #0f172a; margin-top: 0; }
    .guide-card p { color: #64748b; font-size: 0.9rem; margin-bottom: 1rem; }
    .download-btn { background: var(--accent) !important; }
</style>
""", unsafe_allow_html=True)

def main():
    _configure_streamlit()
    _inject_theme()
    
    # Header
    st.markdown("# 📚 Clarivise Documentation")
    st.caption("Download guides for Scan, Shield, and FAQs")
    st.divider()
    
    # Documentation guides
    st.markdown("## Getting Started Guides")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
<div class="guide-card">
  <h3>📧 Clarivise Scan — Quick Start</h3>
  <p>Install the extension, configure your connection, and start analyzing emails in Outlook on the web.</p>
</div>
""", unsafe_allow_html=True)
        if st.button("📥 Download PDF", key="scan_guide", use_container_width=True):
            st.info("PDF download link would appear here")
    
    with col2:
        st.markdown("""
<div class="guide-card">
  <h3>🛡️ Clarivise Shield — Hosted</h3>
  <p>Set up automatic email security on Clarivise servers. Simple mail flow rule in Microsoft 365.</p>
</div>
""", unsafe_allow_html=True)
        if st.button("📥 Download PDF", key="shield_hosted", use_container_width=True):
            st.info("PDF download link would appear here")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("""
<div class="guide-card">
  <h3>☁️ Shield — Self-Hosted Azure</h3>
  <p>Deploy Shield in your own Azure environment. Full control and compliance flexibility.</p>
</div>
""", unsafe_allow_html=True)
        if st.button("📥 Download PDF", key="shield_azure", use_container_width=True):
            st.info("PDF download link would appear here")
    
    with col4:
        st.markdown("""
<div class="guide-card">
  <h3>❓ Frequently Asked Questions</h3>
  <p>Answers to common questions about pricing, features, privacy, and troubleshooting.</p>
</div>
""", unsafe_allow_html=True)
        if st.button("📥 Download PDF", key="faq", use_container_width=True):
            st.info("PDF download link would appear here")
    
    st.divider()
    
    # Additional resources
    st.markdown("## Additional Resources")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 🔗 Quick Links")
        st.markdown("""
- [Clarivise Home](https://clarivise.example.com)
- [Admin Dashboard](https://shield.clarivise.io/dashboard)
- [Privacy Policy](https://clarivise.example.com/privacy)
- [Terms & Conditions](https://clarivise.example.com/terms)
""")
    
    with col_b:
        st.markdown("### 💬 Need Help?")
        st.markdown("""
- **Email:** support@clarivise.io
- **Response time:** 24 hours
- **Chat:** Available in Shield admin dashboard
- **Schedule a call:** calendly.com/clarivise
""")

if __name__ == "__main__":
    main()
