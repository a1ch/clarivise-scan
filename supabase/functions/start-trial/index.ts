// Clarivise — start-trial edge function
// Called from the website signup page.
// Creates an org, generates a token, sets 14-day trial expiry.

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SUPABASE_URL         = Deno.env.get('SUPABASE_URL')!
const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
}

// Block free/personal email providers — we want work emails only
const FREE_DOMAINS = new Set([
  'gmail.com','googlemail.com','yahoo.com','yahoo.ca','yahoo.co.uk',
  'hotmail.com','hotmail.ca','outlook.com','live.com','msn.com',
  'icloud.com','me.com','mac.com','aol.com','protonmail.com',
  'proton.me','tutanota.com','zoho.com','yandex.com','mail.com',
])

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

function generateToken(): string {
  // clarivise-trial-<random hex>
  const bytes = crypto.getRandomValues(new Uint8Array(20))
  const hex = Array.from(bytes).map(b => b.toString(16).padStart(2,'0')).join('')
  return `clarivise-trial-${hex}`
}

async function hashToken(token: string): Promise<string> {
  const enc = new TextEncoder()
  const buf = await crypto.subtle.digest('SHA-256', enc.encode(token))
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,'0')).join('')
}

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS })
  if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405)

  let body: Record<string, string>
  try { body = await req.json() } catch { return json({ error: 'Invalid JSON' }, 400) }

  const { name, email, company } = body

  if (!name?.trim() || !email?.trim() || !company?.trim()) {
    return json({ error: 'Name, email, and company are required.' }, 400)
  }

  const emailLower = email.trim().toLowerCase()
  const domain = extractDomain(emailLower)

  if (!domain) return json({ error: 'Invalid email address.' }, 400)

  if (FREE_DOMAINS.has(domain)) {
    return json({ error: 'Please use your work email address to start a trial.' }, 400)
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

  // Check if this domain already has an org
  const { data: existing } = await supabase
    .from('organizations')
    .select('id, status, trial_ends_at, plan')
    .eq('domain', domain)
    .single()

  if (existing) {
    // Already signed up — check if trial is still active
    const now = new Date()
    const trialEnd = existing.trial_ends_at ? new Date(existing.trial_ends_at) : null
    if (trialEnd && trialEnd > now) {
      return json({ error: `Your organization already has an active trial. Check your inbox for your setup instructions.` }, 409)
    }
    if (existing.plan === 'active') {
      return json({ error: `Your organization is already a Clarivise customer. Contact support@clarivise.ai for help.` }, 409)
    }
    // Expired trial — allow re-signup
  }

  // Create or update org
  const trialEndsAt = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString()
  const slug = domain.replace(/\./g, '-')

  let orgId: string

  if (existing) {
    // Reset expired trial
    const { data: updated, error: updateErr } = await supabase
      .from('organizations')
      .update({
        contact_name: name.trim(),
        contact_email: emailLower,
        company_name: company.trim(),
        plan: 'trial',
        status: 'trial',
        trial_ends_at: trialEndsAt,
      })
      .eq('id', existing.id)
      .select('id')
      .single()

    if (updateErr || !updated) return json({ error: 'Failed to create trial. Please try again.' }, 500)
    orgId = updated.id
  } else {
    const { data: org, error: orgErr } = await supabase
      .from('organizations')
      .insert({
        name: company.trim(),
        slug,
        domain,
        contact_name: name.trim(),
        contact_email: emailLower,
        company_name: company.trim(),
        plan: 'trial',
        status: 'trial',
        trial_ends_at: trialEndsAt,
        seat_limit: 25,
      })
      .select('id')
      .single()

    if (orgErr || !org) {
      console.error('Org insert error:', orgErr)
      return json({ error: 'Failed to create trial. Please try again.' }, 500)
    }
    orgId = org.id
  }

  // Generate token
  const token = generateToken()
  const tokenHash = await hashToken(token)

  // Revoke any existing trial tokens for this org
  await supabase
    .from('extension_tokens')
    .update({ revoked_at: new Date().toISOString() })
    .eq('org_id', orgId)
    .is('revoked_at', null)

  // Insert new token
  const { error: tokenErr } = await supabase
    .from('extension_tokens')
    .insert({
      token_hash: tokenHash,
      label: `Trial — ${company.trim()}`,
      org_id: orgId,
      user_email: emailLower,
      license_type: 'trial',
      expires_at: trialEndsAt,
    })

  if (tokenErr) {
    console.error('Token insert error:', tokenErr)
    return json({ error: 'Failed to generate trial token. Please try again.' }, 500)
  }

  // Return success — in production you'd send a welcome email here
  return json({
    success: true,
    token,
    trial_ends_at: trialEndsAt,
    domain,
    message: `Your 14-day trial is active. Install Clarivise Scan and enter your token in the extension settings.`,
  })
})