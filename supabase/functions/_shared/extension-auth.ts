import type { SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2"

export async function hashToken(token: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(token)
  const hashBuffer = await crypto.subtle.digest("SHA-256", data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("")
}

/** Legacy single secret (EXTENSION_TOKEN) or an active row in extension_tokens. */
export async function isExtensionTokenAllowed(
  supabase: SupabaseClient,
  token: string,
  legacyEnvToken: string | undefined,
): Promise<boolean> {
  if (!token) return false
  const legacy = legacyEnvToken?.trim()
  if (legacy && token === legacy) return true
  const h = await hashToken(token)
  const { data } = await supabase
    .from("extension_tokens")
    .select("id")
    .eq("token_hash", h)
    .is("revoked_at", null)
    .maybeSingle()
  return !!data
}
