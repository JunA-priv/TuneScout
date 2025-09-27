-- スキーマ
SET search_path = public;

-- 必須拡張
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- ← これで gen_random_uuid() が使えるようになる
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 共通: updated_at 自動更新トリガ関数
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 型
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'release_type') THEN
    CREATE TYPE release_type AS ENUM ('album', 'single', 'compilation', 'appears_on', 'unknown');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'confidence_level') THEN
    CREATE TYPE confidence_level AS ENUM ('high', 'medium', 'low', 'unknown');
  END IF;
END$$;

-- ============= ARTISTS =============
CREATE TABLE IF NOT EXISTS artists (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),   -- ← 修正
  spotify_id   text UNIQUE NOT NULL,
  name         text NOT NULL,
  genres       text[] DEFAULT '{}',
  followers    bigint,
  popularity   int,
  spotify_url  text,
  images       jsonb,
  source_raw   jsonb,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_artists_spotify_id ON artists(spotify_id);
CREATE INDEX IF NOT EXISTS idx_artists_name_trgm ON artists USING gin (name gin_trgm_ops);

DROP TRIGGER IF EXISTS trg_artists_updated_at ON artists;
CREATE TRIGGER trg_artists_updated_at
BEFORE UPDATE ON artists
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============= artist_aliases =============
CREATE TABLE IF NOT EXISTS artist_aliases (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  artist_id  uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  alias      text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_artist_alias ON artist_aliases(artist_id, alias);

-- ============= LABELS =============
CREATE TABLE IF NOT EXISTS labels (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name         text UNIQUE NOT NULL,
  country_hint text,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_labels_updated_at ON labels;
CREATE TRIGGER trg_labels_updated_at
BEFORE UPDATE ON labels
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============= RELEASES =============
CREATE TABLE IF NOT EXISTS releases (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  spotify_id             text UNIQUE NOT NULL,
  artist_id              uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  name                   text NOT NULL,
  release_type           release_type NOT NULL DEFAULT 'unknown',
  total_tracks           int,
  release_date           date,
  release_date_precision text,
  spotify_url            text,
  images                 jsonb,
  available_markets      text[] DEFAULT '{}',
  label_id               uuid REFERENCES labels(id),
  label_name_raw         text,
  source_raw             jsonb,
  created_at             timestamptz NOT NULL DEFAULT now(),
  updated_at             timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_releases_spotify_id ON releases(spotify_id);
CREATE INDEX IF NOT EXISTS idx_releases_artist_id ON releases(artist_id);
CREATE INDEX IF NOT EXISTS idx_releases_release_type ON releases(release_type);
CREATE INDEX IF NOT EXISTS idx_releases_release_date ON releases(release_date);

DROP TRIGGER IF EXISTS trg_releases_updated_at ON releases;
CREATE TRIGGER trg_releases_updated_at
BEFORE UPDATE ON releases
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============= release_labels =============
CREATE TABLE IF NOT EXISTS release_labels (
  release_id uuid NOT NULL REFERENCES releases(id) ON DELETE CASCADE,
  label_id   uuid NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
  PRIMARY KEY (release_id, label_id)
);

-- ============= TRACKS =============
CREATE TABLE IF NOT EXISTS tracks (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  spotify_id        text UNIQUE NOT NULL,
  release_id        uuid NOT NULL REFERENCES releases(id) ON DELETE CASCADE,
  artist_id         uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  name              text NOT NULL,
  track_number      int,
  disc_number       int,
  duration_ms       int,
  explicit          boolean,
  isrc              text,
  is_playable       boolean,
  spotify_url       text,
  available_markets text[] DEFAULT '{}',
  external_ids      jsonb,
  source_raw        jsonb,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tracks_spotify_id ON tracks(spotify_id);
CREATE INDEX IF NOT EXISTS idx_tracks_release_id ON tracks(release_id);
CREATE INDEX IF NOT EXISTS idx_tracks_artist_id ON tracks(artist_id);
CREATE INDEX IF NOT EXISTS idx_tracks_isrc ON tracks(isrc);

DROP TRIGGER IF EXISTS trg_tracks_updated_at ON tracks;
CREATE TRIGGER trg_tracks_updated_at
BEFORE UPDATE ON tracks
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============= track_audio_features =============
CREATE TABLE IF NOT EXISTS track_audio_features (
  track_id         uuid PRIMARY KEY REFERENCES tracks(id) ON DELETE CASCADE,
  danceability     numeric,
  energy           numeric,
  key              int,
  loudness         numeric,
  mode             int,
  speechiness      numeric,
  acousticness     numeric,
  instrumentalness numeric,
  liveness         numeric,
  valence          numeric,
  tempo            numeric,
  time_signature   int,
  raw              jsonb,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_track_audio_features_updated_at ON track_audio_features;
CREATE TRIGGER trg_track_audio_features_updated_at
BEFORE UPDATE ON track_audio_features
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============= artist_country_inference =============
CREATE TABLE IF NOT EXISTS artist_country_inference (
  artist_id        uuid PRIMARY KEY REFERENCES artists(id) ON DELETE CASCADE,
  is_japanese      boolean,
  confidence       confidence_level NOT NULL DEFAULT 'unknown',
  top_isrc_country text,
  signals          jsonb,
  explanation      text,
  computed_at      timestamptz NOT NULL DEFAULT now(),
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_artist_country_inference_updated_at ON artist_country_inference;
CREATE TRIGGER trg_artist_country_inference_updated_at
BEFORE UPDATE ON artist_country_inference
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS artist_country_inference_log (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  artist_id       uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  is_japanese     boolean,
  confidence      confidence_level,
  top_isrc_country text,
  signals         jsonb,
  explanation     text,
  computed_at     timestamptz NOT NULL DEFAULT now(),
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- ============= markets =============
CREATE TABLE IF NOT EXISTS release_markets (
  release_id uuid NOT NULL REFERENCES releases(id) ON DELETE CASCADE,
  market     text NOT NULL,
  PRIMARY KEY (release_id, market)
);

CREATE TABLE IF NOT EXISTS track_markets (
  track_id uuid NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
  market   text NOT NULL,
  PRIMARY KEY (track_id, market)
);

-- ============= views =============
CREATE OR REPLACE VIEW v_artist_country_summary AS
SELECT
  a.id              AS artist_id,
  a.name,
  a.genres,
  a.popularity,
  a.followers,
  a.spotify_url,
  ci.is_japanese,
  ci.confidence,
  ci.top_isrc_country,
  ci.signals,
  ci.explanation,
  ci.computed_at
FROM artists a
LEFT JOIN artist_country_inference ci ON ci.artist_id = a.id;

CREATE OR REPLACE VIEW v_artist_isrc_country_counts AS
SELECT
  t.artist_id,
  UPPER(SUBSTRING(t.isrc, 1, 2)) AS country_code,
  COUNT(*) AS track_count
FROM tracks t
WHERE t.isrc IS NOT NULL AND length(t.isrc) >= 2
GROUP BY t.artist_id, UPPER(SUBSTRING(t.isrc, 1, 2));
