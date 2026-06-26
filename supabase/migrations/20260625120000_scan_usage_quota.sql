-- Per-identity monthly scan quota for Edge Function analyze-email.
-- token_key is the same hashed auth subject already used by rate_limit_log / scan_log
-- (sso:<email> for SSO users, or the extension token for token users).
create table if not exists public.scan_usage (
  token_key  text not null,
  period     text not null,                 -- 'YYYY-MM' (UTC)
  count      integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key (token_key, period)
);

alter table public.scan_usage enable row level security;
revoke all on table public.scan_usage from anon, authenticated;

-- Atomic check-and-increment. Reserves a slot ONLY if the caller is under the limit.
-- Returns allowed=false (with the current count) when the cap has been reached, so the
-- Edge Function can skip the Anthropic call entirely.
create or replace function public.increment_scan_usage(
  p_token_key text,
  p_period    text,
  p_limit     integer
)
returns table(allowed boolean, used integer)
language plpgsql
as $$
declare
  cur integer;
begin
  insert into public.scan_usage (token_key, period, count)
  values (p_token_key, p_period, 0)
  on conflict (token_key, period) do nothing;

  -- Lock this identity's row for the period so concurrent scans can't oversell the quota.
  select count into cur
  from public.scan_usage
  where token_key = p_token_key and period = p_period
  for update;

  if cur >= p_limit then
    return query select false, cur;
  else
    update public.scan_usage
      set count = count + 1, updated_at = now()
      where token_key = p_token_key and period = p_period;
    return query select true, cur + 1;
  end if;
end;
$$;

revoke all on function public.increment_scan_usage(text, text, integer) from anon, authenticated;
