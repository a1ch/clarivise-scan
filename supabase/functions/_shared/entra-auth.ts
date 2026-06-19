// Entra (Azure AD) SSO identity-token validation for the Clarivise Scan add-in.
// Config-driven: dev defaults are embedded below; in production set the
// ENTRA_SSO_CONFIG env var (JSON) to add/replace tenants + allowed domains — no code change.
import { jwtVerify, createRemoteJWKSet } from "https://esm.sh/jose@5"

type TenantCfg = { audiences: string[]; domains: string[] }

const DEFAULT_CONFIG: Record<string, TenantCfg> = {
  // Ingot Solutions (dev / test tenant)
  "c9df3cbf-0599-4b61-8ee3-69aa5057ee48": {
    audiences: [
      "7b86ec1f-da7c-45a9-b7db-2ee621db146b",
      "api://a1ch.github.io/7b86ec1f-da7c-45a9-b7db-2ee621db146b",
    ],
    domains: ["ingotsolutions.com"],
  },
}

function loadConfig(): Record<string, TenantCfg> {
  try {
    const raw = Deno.env.get("ENTRA_SSO_CONFIG")
    if (raw) return JSON.parse(raw) as Record<string, TenantCfg>
  } catch (_e) { /* malformed env → use defaults */ }
  return DEFAULT_CONFIG
}
const CONFIG = loadConfig()

const jwksCache: Record<string, ReturnType<typeof createRemoteJWKSet>> = {}
function jwksFor(tid: string) {
  if (!jwksCache[tid]) {
    jwksCache[tid] = createRemoteJWKSet(
      new URL(`https://login.microsoftonline.com/${tid}/discovery/v2.0/keys`),
    )
  }
  return jwksCache[tid]
}

export type EntraResult =
  | { ok: true; email: string; domain: string; tid: string }
  | { ok: false; reason: "invalid_token" | "domain_not_allowed"; email?: string; domain?: string }

export async function verifyEntraToken(token: string): Promise<EntraResult> {
  if (!token) return { ok: false, reason: "invalid_token" }
  for (const tid of Object.keys(CONFIG)) {
    const cfg = CONFIG[tid]
    try {
      const { payload } = await jwtVerify(token, jwksFor(tid), {
        issuer: `https://login.microsoftonline.com/${tid}/v2.0`,
        audience: cfg.audiences,
      })
      const p = payload as Record<string, unknown>
      const email = String(p.preferred_username ?? p.upn ?? p.email ?? "").toLowerCase()
      const domain = email.split("@")[1] ?? ""
      if (cfg.domains.map((d) => d.toLowerCase()).includes(domain)) {
        return { ok: true, email, domain, tid }
      }
      return { ok: false, reason: "domain_not_allowed", email, domain }
    } catch (_e) {
      // signature / issuer / audience mismatch for this tenant — try the next
    }
  }
  return { ok: false, reason: "invalid_token" }
}
