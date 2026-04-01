-- Per-client extension tokens (hashed). Issue plain tokens from the admin-console function only.
create table if not exists public.extension_tokens (
  id uuid primary key default gen_random_uuid(),
  token_hash text not null unique,
  label text,
  created_at timestamptz not null default now(),
  revoked_at timestamptz
);

create index if not exists extension_tokens_active_idx
  on public.extension_tokens (token_hash) where revoked_at is null;

alter table public.extension_tokens enable row level security;

revoke all on public.extension_tokens from anon, authenticated;
grant select, insert, update, delete on public.extension_tokens to service_role;
