-- Optional envelope metadata for support / analytics (no body stored here)
alter table public.scan_log add column if not exists subject text;
alter table public.scan_log add column if not exists sender text;
alter table public.scan_log add column if not exists recipient text;
