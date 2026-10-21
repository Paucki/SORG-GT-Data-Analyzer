-- SORG GT Data Analyzer - gemeinsame Cloud-Datenbank
-- Supabase / PostgreSQL
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default '',
  role text not null default 'user' check (role in ('admin','user')),
  created_at timestamptz not null default now()
);

create table if not exists public.teams (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.team_members (
  team_id uuid not null references public.teams(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'user' check (role in ('admin','user')),
  created_at timestamptz not null default now(),
  primary key(team_id,user_id)
);

create or replace function public.is_team_member(p_team uuid)
returns boolean
language sql stable security definer
set search_path = public
as $$
  select exists(
    select 1 from public.team_members
    where team_id=p_team and user_id=auth.uid()
  );
$$;

create or replace function public.handle_new_user()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
  insert into public.profiles(id,display_name)
  values(new.id,coalesce(new.raw_user_meta_data->>'display_name',split_part(new.email,'@',1)))
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

create table if not exists public.cars (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  start_number text,
  manufacturer text not null default '',
  model text not null default '',
  car_class text,
  year integer default 0,
  weight_kg double precision default 0,
  horsepower double precision default 0,
  drive_type text,
  target_hot_front_bar double precision default 0,
  target_hot_rear_bar double precision default 0,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.drivers (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  first_name text not null default '',
  last_name text not null default '',
  nickname text,
  race_number text,
  licence_class text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.tracks (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  name text not null default '',
  country text,
  length_km double precision default 0,
  corners integer default 0,
  address text,
  latitude double precision,
  longitude double precision,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.events (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  name text not null default '',
  track_id uuid not null references public.tracks(id) on delete restrict,
  start_date date,
  end_date date,
  championship text,
  event_type text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.sessions (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  event_id uuid not null references public.events(id) on delete cascade,
  car_id uuid not null references public.cars(id) on delete restrict,
  driver_id uuid references public.drivers(id) on delete set null,
  session_type text,
  session_date timestamptz,
  weather text,
  air_temp_c double precision default 0,
  track_temp_c double precision default 0,
  rim_temp_c double precision default 0,
  humidity_percent double precision default 0,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.session_drivers (
  session_id uuid not null references public.sessions(id) on delete cascade,
  driver_id uuid not null references public.drivers(id) on delete cascade,
  primary key(session_id,driver_id)
);

create table if not exists public.tyre_sets (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  session_id uuid not null references public.sessions(id) on delete cascade,
  set_number text not null default '',
  manufacturer text,
  compound text,
  tyre_type text default 'Slick',
  condition text default 'gebraucht',
  laps integer default 0,
  heat_cycles integer default 0,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.tyre_measurements (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  tyre_set_id uuid not null references public.tyre_sets(id) on delete cascade,
  position text not null check(position in ('FL','FR','RL','RR')),
  cold_pressure_bar double precision,
  hot_pressure_bar double precision,
  target_pressure_bar double precision,
  temp_inside_c double precision,
  temp_middle_c double precision,
  temp_outside_c double precision,
  wear_percent double precision,
  cold_tyre_temp_c double precision,
  expected_hot_tyre_temp_c double precision,
  ambient_pressure_bar double precision default 1.01325,
  calculated_cold_pressure_bar double precision,
  calibration_offset_bar double precision default 0,
  calculation_model text,
  driven_cold_pressure_bar double precision,
  pressure_difference_bar double precision,
  reference_cold_pressure_bar double precision,
  recommended_next_cold_pressure_bar double precision,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz,
  unique(tyre_set_id,position)
);

create table if not exists public.session_changes (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  session_id uuid not null references public.sessions(id) on delete cascade,
  category text,
  title text,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.session_setup_entries (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  session_id uuid not null references public.sessions(id) on delete cascade,
  category text not null,
  parameter_name text not null,
  old_value text,
  new_value text,
  unit text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz
);

create table if not exists public.session_media (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  session_id uuid not null references public.sessions(id) on delete cascade,
  title text not null,
  file_path text not null,
  media_type text,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.driver_track_pressure_targets (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  driver_id uuid not null references public.drivers(id) on delete cascade,
  track_id uuid not null references public.tracks(id) on delete cascade,
  car_id uuid not null references public.cars(id) on delete cascade,
  target_hot_front_bar double precision not null,
  target_hot_rear_bar double precision not null,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz,
  unique(driver_id,track_id,car_id)
);

create table if not exists public.pressure_recommendation_log (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  tyre_set_id uuid not null references public.tyre_sets(id) on delete cascade,
  position text not null,
  target_hot_pressure_bar double precision,
  cold_tyre_temp_c double precision,
  expected_hot_tyre_temp_c double precision,
  ambient_pressure_bar double precision,
  history_correction_bar double precision,
  recommended_cold_pressure_bar double precision,
  model_version text,
  created_at timestamptz not null default now()
);

create table if not exists public.tyre_notes (
  id uuid primary key default gen_random_uuid(),
  legacy_id bigint,
  team_id uuid not null references public.teams(id) on delete cascade,
  tyre_set_id uuid not null references public.tyre_sets(id) on delete cascade,
  note_time timestamptz not null default now(),
  action text,
  tyre_type text,
  manufacturer text,
  condition_before text,
  condition_after text,
  notes text
);

-- Row Level Security: nur Mitglieder desselben Teams sehen/ändern Teamdaten.
alter table public.profiles enable row level security;
alter table public.teams enable row level security;
alter table public.team_members enable row level security;

create policy "own profile read" on public.profiles for select using (id=auth.uid());
create policy "team read" on public.teams for select using (public.is_team_member(id));
create policy "team members read" on public.team_members for select using (public.is_team_member(team_id));

do $$
declare t text;
begin
  foreach t in array array[
    'cars','drivers','tracks','events','sessions','tyre_sets','tyre_measurements',
    'session_changes','session_setup_entries','session_media',
    'driver_track_pressure_targets','pressure_recommendation_log','tyre_notes'
  ]
  loop
    execute format('alter table public.%I enable row level security',t);
    execute format('create policy "team_select" on public.%I for select using (public.is_team_member(team_id))',t);
    execute format('create policy "team_insert" on public.%I for insert with check (public.is_team_member(team_id))',t);
    execute format('create policy "team_update" on public.%I for update using (public.is_team_member(team_id)) with check (public.is_team_member(team_id))',t);
    execute format('create policy "team_delete" on public.%I for delete using (public.is_team_member(team_id))',t);
  end loop;
end $$;

-- Sinnvolle Indizes
create index if not exists idx_sessions_event on public.sessions(event_id);
create index if not exists idx_tyre_sets_session on public.tyre_sets(session_id);
create index if not exists idx_tyre_measurements_set on public.tyre_measurements(tyre_set_id);
create index if not exists idx_events_team on public.events(team_id);
create index if not exists idx_sessions_team on public.sessions(team_id);
create index if not exists idx_measurements_team on public.tyre_measurements(team_id);
