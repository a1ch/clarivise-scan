// Clarivise — auto-auth edge function
// Called by the extension on startup with the user's email/domain.
// Returns a session token if the org has an active trial or subscription.
// This replaces manual key entry for orgs that signed up via the website.

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SUPABASE_URL         = Deno.env.get('SUPABASE_URL')!
const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS },
  })
}

function extractDomain(email: string): string {
  const match = email.toLowerCase().trim().match(/@([\w.-]+)$/)
  return match ? match[1] : ''
}

async function hashToken(token: string): Promise<string> {
  const enc = new TextEncoder()
  const buf = await crypto.subtle.digest('SHA-256', enc.encode(token))
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,'0')).join('')
}

function generateSessionToken(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(20))
  const hex = Array.from(bytes).map(b => b.toString(16).padStart(2,'0')).join('')
  return `clarivise-sess-${hex}`
}

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS })
  if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405)

  let body: Record<string, string>
  try { body = await req.json() } catch { return json({ error: 'Invalid JSON' }, 400) }

  const { email } = body
  if (!email?.trim()) return json({ error: 'Email is required.' }, 400)

  const domain = extractDomain(email)
  if (!domain) return json({ error: 'Invalid email address.' }, 400)

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

  // Look up org by domain
  const { data: org } = await supabase
    .from('organizations')
    .select('id, name, plan, status, trial_ends_at, seat_limit')
    .eq('domain', domain)
    .single()

  if (!org) {
    return json({
      error: 'No Clarivise trial or subscription found for your organization.',
      action: 'signup',
    }, 404)
  }

  // Check trial/subscription status
  const now = new Date()

  if (org.status === 'cancelled') {
    return json({ error: 'Your Clarivise subscription has been cancelled. Contact support@clarivise.ai.' }, 403)
  }

  if (org.plan === 'trial') {
    const trialEnd = org.trial_ends_at ? new Date(org.trial_ends_at) : null
    if (!trialEnd || trialEnd < now) {
      const daysAgo = trialEnd ? Math.floor((now.getTime() - trialEnd.getTime()) / 86400000) : null
      return json({
        error: `Your 14-day trial has expired${daysAgo ? ` (${daysAgo} days ago)` : ''}. Upgrade at clarivise.ai to continue.`,
        action: 'upgrade',
        trial_ended_at: trialEnd?.toISOString(),
      }, 403)
    }
  }

  // Org is active — generate a short-lived session token (24h)
  // and store its hash so analyze-email can validate it
  const sessionToken = generateSessionToken()
  const sessionHash = await hashToken(sessionToken)
  const sessionExpiry = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()

  const { error: insertErr } = await supabase
    .from('extension_tokens')
    .insert({
      token_hash: sessionHash,
      label: `Auto-auth session — ${email.trim().toLowerCase()}`,
      org_id: org.id,
      user_email: email.trim().toLowerCase(),
      license_type: org.plan,
      expires_at: sessionExpiry,
    })

  if (insertErr) {
    console.error('Session token insert error:', insertErr)
    return json({ error: 'Failed to authenticate. Please try again.' }, 500)
  }

  const trialEnd = org.trial_ends_at ? new Date(org.trial_ends_at) : null
  const daysRemaining = trialEnd
    ? Math.max(0, Math.ceil((trialEnd.getTime() - now.getTime()) / 86400000))
    : null

  return json({
    success: true,
    token: sessionToken,
    session_expires_at: sessionExpiry,
    org_name: org.name,
    plan: org.plan,
    trial_ends_at: org.trial_ends_at,
    days_remaining: daysRemaining,
    message: org.plan === 'trial'
      ? `Trial active — ${daysRemaining} day${daysRemaining === 1 ? '' : 's'} remaining.`
      : 'Subscription active.',
  })
})