# Email Evaluator — self-serve product key portal (Streamlit)

Small web UI where approved users request a **Chrome extension product key**. The app includes **product and setup documentation** (expandable sections) plus the signup form. Each signup creates a row in **`customers`**, then a row in **`extension_tokens`** with **`customer_id`** set (see migration `20260406120000_customers.sql`). Keys are still stored hashed.

**Optional white-label (Streamlit secrets):** `PORTAL_PRODUCT_NAME`, `PORTAL_BRAND_NAME`, `PORTAL_TAGLINE` (hero subhead), `PORTAL_COMPANY_URL`, `PORTAL_GITHUB_URL` — used in the marketing hero and help text on the page.

**You do not need to run this on your PC for end users.** Host it on **Streamlit Community Cloud** (free tier available) so everyone gets a normal **https://** URL.

**Home vs. key flow:** The app uses Streamlit **multipage** navigation. The **sidebar is expanded by default** and lists **streamlit_app** (marketing home) and **Request_a_key** (sign-in + form). The main column also has **Home** and **Request a key** links (`st.page_link`, Streamlit ≥1.33). Users can click **Get a product key** on the home page to jump to the key page. To open the key flow from a URL, use `?page=key` on the home URL or open the **Request_a_key** page from the sidebar. Set Supabase **Authentication → URL Configuration → Site URL** to your app’s **root** (e.g. `https://your-app.streamlit.app`).

---

## Deploy on Streamlit Community Cloud (recommended)

1. **Push this repo to GitHub** (the `portal/` folder must be in the repo).

2. Sign in at **[share.streamlit.io](https://share.streamlit.io)** with GitHub.

3. Click **New app** → choose the repo and branch.

4. **Main file path:** leave the default **`streamlit_app.py`** (at the **repository root**).  
   That file loads the UI from **`portal/app.py`**.  
   Dependencies are installed from the root **`requirements.txt`** (also required for this layout).

5. In Supabase, enable **Email** under **Authentication → Sign-in / Providers** and set **Site URL** to your Streamlit app URL (e.g. `https://your-app.streamlit.app`). Users **create an account** or **sign in** on the portal; the **work email** on the key request is the Auth email.

6. Open **⚙ Settings** → **Secrets**. Paste TOML with **exact** keys `SUPABASE_URL`, **`SUPABASE_ANON_KEY`** (anon or publishable key from the API page), and **`SUPABASE_SERVICE_ROLE_KEY`** (see **`.streamlit/secrets.toml.example`** at the **repo root**):

   ```toml
   SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
   SUPABASE_ANON_KEY = "eyJ... anon or publishable"
   SUPABASE_SERVICE_ROLE_KEY = "eyJ... service_role"

   DEFAULT_ORG_ID = ""
   PORTAL_SIGNUP_SECRET = "your-long-random-phrase"
   ```

   - **`DEFAULT_ORG_ID`:** optional UUID from `select id from public.organizations`. Leave `""` to auto-create an org per signup.
   - **`PORTAL_SIGNUP_SECRET`:** strongly recommended so random people cannot mint keys.

7. **Deploy.** When the app is live, share the **`*.streamlit.app`** URL with your users.

8. **Database:** run **`npx supabase db push`** (or apply migrations) so `customers` includes **`auth_user_id`** (links portal users to `auth.users`).

9. **Updates:** push to GitHub; the app can be set to redeploy automatically on commit.

---

## Security (hosted)

- The **service role** key lives only in **Streamlit Secrets**, never in the browser.
- The **anon** key is in secrets for **Supabase Auth** only; it is not a substitute for the service role and does not grant table access on its own in this app (inserts still use the service role server-side).
- Use **`PORTAL_SIGNUP_SECRET`** (and rotate it) like a shared invite code in addition to login if the app URL is public.
- Sessions are **Streamlit + Supabase refresh tokens** in `st.session_state` (per browser session), not a replacement for org-wide IdP SSO.

---

## Optional: run on your laptop (development only)

Use this to test UI changes before deploying.

**Secrets file location:** from the **repository root** (where `streamlit_app.py` lives), copy **`.streamlit/secrets.toml.example`** → **`.streamlit/secrets.toml`** and edit. Then:

```bash
# repo root
pip install -r requirements.txt
streamlit run streamlit_app.py
```

If you run `streamlit run portal/app.py` from the repo root without fixing paths, put **`portal/.streamlit/secrets.toml`** instead — but the documented flow is root `streamlit_app.py` + root `.streamlit/secrets.toml`.

---

## After signup

Users paste the key in the extension → **Connection** → **Extension Token**. Trial keys expire in **15 days**, annual in **365 days**, matching the Edge Functions.
