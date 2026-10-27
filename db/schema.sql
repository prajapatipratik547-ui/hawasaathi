-- HawaSaathi database schema for Supabase (Postgres).
-- Run this once in the Supabase SQL Editor. Safe to run again.

create table if not exists users (
  telegram_id    bigint primary key,
  chat_id        bigint,
  language       text check (language in ('en', 'hi', 'mr')),
  state          text,
  lat            double precision,
  lng            double precision,
  area_name      text,
  age_group      text check (age_group in ('child', 'adult', 'senior')),
  condition      text check (condition in ('none', 'lung', 'heart', 'pregnant')),
  outdoor_worker boolean,
  alert_time     time not null default '07:00',
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table if not exists alerts (
  id          bigint generated always as identity primary key,
  telegram_id bigint not null references users (telegram_id) on delete cascade,
  type        text not null check (type in ('morning', 'spike')),
  aqi         integer,
  category    text,
  sent_at     timestamptz not null default now()
);

create table if not exists feedback (
  id           bigint generated always as identity primary key,
  alert_id     bigint not null references alerts (id) on delete cascade,
  telegram_id  bigint not null references users (telegram_id) on delete cascade,
  changed_plan boolean not null,
  answered_at  timestamptz not null default now()
);

-- only one impact answer per alert
create unique index if not exists feedback_one_per_alert on feedback (alert_id);

create table if not exists questions (
  id          bigint generated always as identity primary key,
  telegram_id bigint not null references users (telegram_id) on delete cascade,
  question    text not null,
  answered_at timestamptz not null default now()
);

-- Row Level Security on, with no policies: the public (anon) key can't read or
-- write anything. Only our server's service/secret key can, because it bypasses RLS.
alter table users     enable row level security;
alter table alerts    enable row level security;
alter table feedback  enable row level security;
alter table questions enable row level security;

-- Make sure the server key can use the tables and their id sequences.
grant select, insert, update, delete on users, alerts, feedback, questions to service_role;
grant usage, select on all sequences in schema public to service_role;
