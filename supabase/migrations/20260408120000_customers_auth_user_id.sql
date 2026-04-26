-- Link portal signups to Supabase Auth (auth.users).

alter table public.customers
  add column if not exists auth_user_id uuid references auth.users (id) on delete set null;

-- At most one customer row per login user per organization (e.g. second company = second row).
create unique index if not exists customers_auth_user_id_org_id_unique
  on public.customers (auth_user_id, org_id)
  where auth_user_id is not null;

comment on column public.customers.auth_user_id is 'Set when the row was created by a logged-in Supabase Auth user.';
