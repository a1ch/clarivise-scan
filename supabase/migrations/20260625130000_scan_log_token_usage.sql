-- Capture per-scan Anthropic token usage so prompt-cache effectiveness and real
-- cost can be measured. Populated by Edge Function analyze-email from response.usage.
alter table public.scan_log add column if not exists input_tokens integer;
alter table public.scan_log add column if not exists output_tokens integer;
alter table public.scan_log add column if not exists cache_read_input_tokens integer;
alter table public.scan_log add column if not exists cache_creation_input_tokens integer;
