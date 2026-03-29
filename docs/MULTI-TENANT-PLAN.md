# Multi-tenant plan — Outlook Email Evaluator

This document outlines how to evolve the product so **multiple customer organizations** can use it safely and independently. It is a planning artifact; implementation order can change based on your go-to-market.

## What “multi-tenant” means here

| Layer | Today (single-tenant) | Multi-tenant goal |
|--------|------------------------|------------------|
| **Extension** | One proxy URL + one shared token per install | Per-tenant (or per-user) backend identity and config |
| **Supabase** | One project, one `EXTENSION_TOKEN`, shared DB | Isolated data and/or isolated projects per customer |
| **AI / cost** | One Anthropic key (your cost) | Per-tenant keys, quotas, or pooled billing |
| **Microsoft** | N/A or one Entra app | Optional: each customer’s Entra tenant, or multi-tenant app |

Clarify your product shape:

- **B2B SaaS:** You operate one platform; many companies subscribe; you need strong **logical isolation** and often **per-tenant admin**.
- **White-label / self-hosted:** Each customer runs **their own** Supabase (and extension pointed at their URL) — “multi-tenant” is mostly **documentation and packaging**, not one shared database.
- **Hybrid:** Shared control plane + optional dedicated Supabase per enterprise.

---

## Which side is easier? (planning summary)

Use this when choosing **where to start** and **which isolation model** to favor.

### A. Isolation model: shared DB + RLS vs one Supabase project per tenant

| Criterion | **Shared DB + RLS** | **Project per tenant** |
|-----------|---------------------|-------------------------|
| **Avoiding cross-tenant data leaks** | **Harder** — one RLS/policy bug can affect every customer | **Easier** — separate DB, network, and keys; failures are contained |
| **Day-2 operations** (deploys, logs, upgrades) | **Easier** — one project, one pipeline | **Harder** — N projects unless you automate provisioning |
| **Central analytics / admin** | **Easier** — one SQL database | **Harder** — aggregate from N projects or ship events to a warehouse |
| **Solo / small team early on** | Medium — invest in RLS tests + security review | Medium–high — either heavy automation or manual project sprawl |

**Plain language:** If the priority is **“I can’t afford a cross-tenant mistake,”** **separate projects (B) is the easier mental model**. If the priority is **“I can’t afford to operate N Supabase projects,”** **shared DB + RLS (A) is the easier operational model** — with the tradeoff that correctness is on you.

### B. Extension vs server: what to build first

| Lead with | Usually **easier** for… | Risk |
|-----------|-------------------------|------|
| **Server first** (Auth, `tenants`, JWT claims, Edge Function accepting Bearer, RLS drafts) | **Correctness** — test with curl/Postman/SQL without Chrome OAuth, MV3 sleep, or redirect URI issues | Extension UI comes later; fewer stakeholder-visible demos early |
| **Extension first** (Sign in with Microsoft, store tokens, call API) | **Demos** — people see login working in the browser | API and claims may change → **rework** in the popup and storage |

**Plain language:** For a **solid multi-tenant v1**, **backend-first is generally easier** than fighting the extension while the contract is still moving.

### C. SSO vs tenant data model: ordering

| Order | Easier for… |
|-------|-------------|
| **Define `tenants` + what goes in the JWT (`tenant_id`, role) → then wire Microsoft SSO** | Clear target for Auth hooks and RLS before you touch `launchWebAuthFlow` |
| **SSO first → default single tenant for everyone → later split tenants** | **Fastest path to “someone signed in”**; you add real tenant boundaries in a second phase |

**Practical compromise:** **SSO + one synthetic “default” tenant** for all early users, then **introduce real `tenant_id` and RLS** before you onboard a second paying org — often the **easiest emotional arc** (working auth first, isolation before scale).

---

The sections below assume **B2B SaaS on a shared Supabase project** unless noted.

---

## 1. Tenant isolation models (pick one primary strategy)

### A. Shared Supabase, row-level multi-tenancy (RLS)

- Single Postgres database; every table that holds tenant data has **`tenant_id` (uuid)`**.
- **RLS policies** enforce `tenant_id = current_setting('request.jwt.claims', ...)::json->>'tenant_id'` (or equivalent) using Supabase Auth JWT custom claims.
- **Pros:** One deployment, one billing for infra, easier feature rollout.  
- **Cons:** RLS must be correct on **every** table and function; bugs are high impact. Requires **authenticated users** (SSO) or a signed tenant context.

### B. Supabase project per tenant

- Each customer gets `https://<ref>.supabase.co` + their own secrets and migrations.
- Extension stores **per-tenant proxy URL** (already possible manually); you add **tenant discovery** (login → which backend).
- **Pros:** Hard isolation, blast radius small.  
- **Cons:** Operational overhead (N projects), harder centralized reporting unless you aggregate.

### C. Hybrid

- Small customers on **shared DB + RLS**; enterprise on **dedicated project** (or schema) via feature flag.

**Recommendation for a growing SaaS:** start planning around **A (RLS)** for app data, keep **B** as an enterprise tier if needed.

---

## 2. Identity and “who is the tenant?”

Without SSO, a shared `EXTENSION_TOKEN` cannot distinguish tenants. Multi-tenant almost always implies:

1. **Supabase Auth** (e.g. Microsoft SSO — implement alongside or after this plan; see team SSO spec).
2. JWT includes **`tenant_id`** (and optionally `role`: admin | member):
   - Set via **Auth Hook** or **custom claims** after first login (map email domain → tenant, or invite flow).

Flows to design:

- **Signup / invite:** Admin creates tenant → invites users → users sign in with Microsoft → claim includes `tenant_id`.
- **Domain claim:** `@acme.com` maps to tenant `acme` (risky if domains collide; prefer explicit invite).
- **Service accounts:** Break-glass API keys per tenant for automation (hashed, rate-limited) — optional.

---

## 3. Data model (sketch)

Add a **`tenants`** table:

- `id` (uuid, PK), `name`, `slug`, `created_at`, `plan`, `settings` (jsonb) — e.g. default `customPrompt` overrides, feature flags.

Add **`tenant_id`** to:

- `scan_log`, `user_feedback`, `rate_limit_log` (or replace token hash with `user_id` + `tenant_id`).

**RLS:**

- `tenants`: readable by members of that tenant only; super-admin bypass via service role (dashboard only).
- Child tables: `tenant_id` match JWT claim.

**Edge Functions:**

- Use **user JWT** for user calls; use **service role** only inside the function after verifying the user belongs to the tenant for the operation.

---

## 4. Configuration per tenant

| Setting | Single-tenant today | Multi-tenant approach |
|---------|----------------------|------------------------|
| Org domain (`tenantDomain`) | Extension setting | Prefer **server-side** default per `tenants.settings` + optional user override |
| Custom prompt | Extension → API | Store **tenant defaults** in DB; merge with user/org overrides |
| Anthropic key | One secret | **Per-tenant secret** in vault table (encrypted) or **your** key with per-tenant budget (simpler ops) |
| Extension proxy URL | User pastes URL | **One** SaaS URL: `https://<your>.supabase.co/functions/v1/analyze-email` + tenant from JWT |

---

## 5. Extension UX (multi-tenant)

1. **Sign in with Microsoft** (or email magic link) → receive Supabase session.
2. **No manual proxy URL** for most users — hardcode or discover your production Supabase project URL in the build (or remote config endpoint).
3. **Optional:** “Advanced” for self-hosted: still allow custom proxy URL (enterprise).
4. **Tenant switcher:** only if users belong to multiple tenants (rare in v1; defer).

---

## 6. Microsoft / Entra in multi-tenant mode

- **Multi-tenant Entra app:** any org can consent; you map `tid` (tenant id) + `oid` / email to your `tenant_id`.
- **Single-tenant apps per customer:** maximum isolation; heavy ops — usually only for largest deals.

For SaaS, **one multi-tenant Entra app** + **your** Supabase Auth Microsoft provider is typical.

---

## 7. Rate limits, abuse, and cost

- Rate limit by **`tenant_id`** and **`user_id`** (not only hashed extension token).
- **Per-tenant quotas:** scans/day in `tenants` or usage table; enforce in Edge Function before Anthropic call.
- **Cost attribution:** log `tenant_id` on every scan for internal billing or show-back reports.

---

## 8. Phased roadmap (suggested)

| Phase | Outcome |
|-------|---------|
| **M0 — Decide** | Choose isolation model (RLS vs project-per-tenant); define “tenant” (company vs workspace). |
| **M1 — Tenants table + RLS** | Add `tenants`, migrate existing data to a default tenant; service-role only writes. |
| **M2 — SSO** | Supabase Auth + Microsoft; JWT with `tenant_id`; Edge Functions accept Bearer. |
| **M3 — Extension** | Sign-in UI; remove or hide proxy URL for SaaS builds; send Bearer on every request. |
| **M4 — Per-tenant settings** | Prompt defaults, org domain, optional per-tenant API key storage. |
| **M5 — Admin / billing** | Tenant admin portal, usage, Stripe (or equivalent), enterprise project split if needed. |

---

## 9. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| RLS misconfiguration | Security review, automated tests, least privilege, staging pen-test |
| Cross-tenant data in logs | Never log raw email body; include only `tenant_id` + metadata you already use |
| Token / key leakage | Short-lived JWTs, no long-lived shared secrets in extension for SaaS users |
| One noisy tenant hurts others | Per-tenant rate limits and optional noisy-neighbor caps on Anthropic spend |

---

## 10. Open decisions (fill in before build)

1. **Isolation:** Shared DB + RLS, or project-per-tenant, or hybrid?  
2. **Who pays Anthropic:** You (metered) vs customer brings key?  
3. **Minimum viable tenant:** Invite-only vs self-service signup?  
4. **Compliance:** Data residency (region), BAA, DPA — may force dedicated regions or projects.  
5. **Outlook-only:** Still true — no change, but SSO redirect URIs must work inside extension constraints.

---

## Related docs

- **[`MULTI-TENANT-AUTH-PLAN.md`](./MULTI-TENANT-AUTH-PLAN.md)** — phased plan for Microsoft login + `tenant_id` in JWT + extension changes.
- `PRIVACY.md` — must be updated when tenant identity and processors change.

**Last updated:** planning doc; adjust dates when you commit milestones.
