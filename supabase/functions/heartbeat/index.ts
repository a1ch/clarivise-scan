// Clarivise — heartbeat edge function
// Called silently by the Scan extension on startup.
// Records the logged-in user's email against their org for seat tracking.
// Zero friction — user never sees this happening.

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SUPABASE_URL         = Deno.env.get('SUPABASE_URL')!
const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
}

// Autoreply/noreply patterns — these should not count as seats
const AUTOREPLY_PATTERNS = [
  /^noreply@/i, /^no-reply@/i, /^donotreply@/i, /^do-not-reply@/i,
  /^mailer-daemon@/i, /^postmaster@/i, /^bounce@/i, /^bounces@/i,
  /^notifications?@/i, /^alerts?@/i, /^automated?@/i,
]

function isAutoreply(email: string): boolean {
  return AUTOREPLY_PATTERNS.some(p => p.test(email))
}

function extractDomain(email: string): string {
  const match = email.toLowerCase().trim().match(/@([\w.-]+)$/)
  return match ? match[1] : ''
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS },
  })
}

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS })
  if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405)

  let body: Record<string, string>
  try { body = await req.json() } catch { return json({ error: 'Invalid JSON' }, 400) }

  const { email, token } = body
  if (!email?.trim() || !token?.trim()) return json({ error: 'email and token required' }, 400)

  const emailLower = email.trim().toLowerCase()
  const domain = extractDomain(emailLower)
  if (!domain) return json({ error: 'Invalid email' }, 400)

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

  // Look up org by domain — checks org_domains table so multi-domain orgs work
  const { data: orgDomain } = await supabase
    .from('org_domains')
    .select('org_id')
    .eq('domain', domain)
    .single()

  // Fall back to legacy domain column on organizations table
  let orgId: string | null = orgDomain?.org_id ?? null

  if (!orgId) {
    const { data: org } = await supabase
      .from('organizations')
      .select('id')
      .eq('domain', domain)
      .single()
    orgId = org?.id ?? null
  }

  if (!orgId) {
    // Unknown domain — silent fail, don't error (org may not have signed up yet)
    return json({ ok: true, known: false })
  }

  // Check trial/subscription is still active
  const { data: org } = await supabase
    .from('organizations')
    .select('plan, status, trial_ends_at, seat_limit')
    .eq('id', orgId)
    .single()

  if (!org) return json({ ok: true, known: false })

  const now = new Date()
  if (org.plan === 'trial' && org.trial_ends_at && new Date(org.trial_ends_at) < now) {
    return json({ ok: true, known: true, trial_expired: true })
  }

  // Upsert the user — update last_seen and increment scan_count
  const autoReply = isAutoreply(emailLower)
  const { error: upsertErr } = await supabase
    .from('org_users')
    .upsert(
      {
        org_id: orgId,
        email: emailLower,
        domain,
        last_seen: now.toISOString(),
        is_autoreply: autoReply,
      },
      {
        onConflict: 'org_id,email',
        ignoreDuplicates: false,
      }
    )

  if (upsertErr) {
    console.error('org_users upsert error:', upsertErr)
    // Don't fail the heartbeat over a tracking error
  }

  // Check seat count against limit
  const { data: seatData } = await supabase
    .from('org_active_seats')
    .select('active_seats')
    .eq('org_id', orgId)
    .single()

  const activeSeats = seatData?.active_seats ?? 0
  const overLimit = org.seat_limit && activeSeats > org.seat_limit

  return json({
    ok: true,
    known: true,
    org_id: orgId,
    plan: org.plan,
    active_seats: activeSeats,
    seat_limit: org.seat_limit,
    over_limit: overLimit,
    is_autoreply: autoReply,
  })
})
