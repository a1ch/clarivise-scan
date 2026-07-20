-- Production-readiness security hardening (applied 2026-07-17, project pikplhvawbhndijpkdbq)
-- Locks down SECURITY DEFINER RPC surface + strips leftover anon table grants.
-- Every statement is idempotent and safe to re-run.

-- 1) Pin search_path on the quota function (was role-mutable -> search_path hijack risk).
alter function public.increment_scan_usage(text, text, integer) set search_path = public, pg_temp;

-- 2) snapshot_security_history(): cron/service-role writer, not a public RPC.
revoke execute on function public.snapshot_security_history() from anon, authenticated, public;
grant  execute on function public.snapshot_security_history() to service_role;

-- 3) ops_health() + security_hub_stats(): called ONLY by service-role edge functions.
--    They were exposing org-wide security data + phishing-target emails to anon. Remove it.
revoke execute on function public.ops_health() from anon, authenticated, public;
revoke execute on function public.security_hub_stats(integer, text) from anon, authenticated, public;
revoke execute on function public.security_hub_stats(integer, text, text) from anon, authenticated, public;
grant  execute on function public.ops_health() to service_role;
grant  execute on function public.security_hub_stats(integer, text) to service_role;
grant  execute on function public.security_hub_stats(integer, text, text) to service_role;

-- 4) Strip leftover anon/authenticated table grants (RLS deny-all already blocked rows;
--    the grant itself is a latent leak). Backend runs as service_role (unaffected).
revoke all on public.org_domains, public.org_users, public.security_history from anon, authenticated;