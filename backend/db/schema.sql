-- ════════════════════════════════════════════════════════════════════
--  Traviante Visual Search — Supabase Postgres schema
--  Run this in the Supabase SQL editor before indexing destinations.
-- ════════════════════════════════════════════════════════════════════

-- ── Destinations ────────────────────────────────────────────────────
create table if not exists destinations (
  id            text primary key,                 -- slug, e.g. 'bali-ubud'
  name          text not null,
  country       text not null default '',
  tagline       text not null default '',
  description   text not null default '',
  images        text[] not null default '{}',     -- Cloudinary URLs
  price_min_inr integer not null check (price_min_inr >= 0),
  price_max_inr integer not null check (price_max_inr >= 0),
  best_months   text[] not null default '{}',     -- ['october','november',...]
  travel_styles text[] not null default '{}',     -- ['honeymoon','beach',...]
  highlights    text[] not null default '{}',
  is_active     boolean not null default true,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists idx_destinations_active on destinations (is_active);

-- ── Search analytics — this table is GOLD ───────────────────────────
create table if not exists search_events (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  search_type text not null,            -- 'image' | 'text'
  query_text  text,                     -- for text searches
  filters     jsonb,                    -- {budget_max, month, style, group_size}
  result_ids  text[],                   -- top-k destination IDs returned
  clicked_id  text,                     -- which card the user clicked
  converted   boolean not null default false,  -- did they hit "Get Quote"?
  session_id  text
);

create index if not exists idx_search_events_created on search_events (created_at);
create index if not exists idx_search_events_type on search_events (search_type);

-- ── Analytics views ─────────────────────────────────────────────────

-- Daily search → conversion rate.
create or replace view search_conversion_rate as
select
  date_trunc('day', created_at)                       as day,
  count(*)                                             as searches,
  count(*) filter (where converted)                    as conversions,
  round(
    100.0 * count(*) filter (where converted) / nullif(count(*), 0), 2
  )                                                    as conversion_pct
from search_events
group by 1
order by 1 desc;

-- Most common text queries.
create or replace view top_searched_queries as
select query_text, count(*) as searches
from search_events
where query_text is not null and query_text <> ''
group by query_text
order by searches desc
limit 50;

-- ── Row Level Security ──────────────────────────────────────────────
alter table destinations enable row level security;

-- Public (anon) can only read active destinations.
create policy "public reads active destinations"
  on destinations for select
  using (is_active = true);

-- search_events: inserts handled server-side with the service-role key,
-- so no anon policies are granted here.
alter table search_events enable row level security;
