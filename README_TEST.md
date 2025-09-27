# テスト/デバッグ用スクリプトの使い方（test/）

`test/` フォルダ配下にある Python スクリプトの用途と実行方法をまとめています。軽い動作確認、アドホックなデバッグ、簡易的な統合テストに利用できます。

## 概要

- 配置場所: `test/`
- 種類:
  - 直接 `python` で実行できる確認用スクリプト（例: `check_db.py`, `check_artist_data.py`, `check_spotify_data.py`, `get_related_artists.py`）
  - Pytest 形式のテスト（`test_*.py`）: 外部 API やスクレイパーを呼ぶ統合テスト寄りの内容が多いです

## 前提条件

- Python 3.12（`.python-version` を参照）
- 仮想環境の利用を推奨
- `.env` に必要な環境変数を設定（`.env.example` 参照）。最低限（Spotify/Supabase）:
  - `spotify_client_id`, `spotify_client_secret`
  - `supabase_url`, `supabase_key`, `supabase_service_key`
  - 任意: `database_url`（未設定の場合は `sqlite:///./test.db` を使用）

### 依存関係のインストール

pip を利用する場合:
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -U pip`
- `pip install -e .`

uv を利用する場合（任意）:
- `uv venv && source .venv/bin/activate`
- `uv pip install -e .`
- 開発ツール（pytest/ruff/black）: 必要に応じて個別にインストール

注: 一部スクリプトは外部サービス（Spotify、各種サイト）にアクセスします。ネットワークと認証情報の準備が必要です。

## 個別スクリプトの実行（確認/デバッグ）

- `python test/check_db.py`
  - 設定済みの DB に接続し、アーティスト件数と一部レコードを表示
  - `packages.common.db` を使用。`database_url` 未設定時は `sqlite:///./test.db` を使用

- `python test/check_artist_data.py`
  - DB 内の最大 5 件のアーティスト詳細（名前、人気度、フォロワー、ジャンル、外部 URL）を表示

- `python test/check_spotify_data.py`
  - Spotify から日本の新譜を取得してサンプルを表示
  - 取得データ全体をプロジェクト直下の `spotify_data_sample.json` に保存
  - `spotify_client_id` と `spotify_client_secret` が必須

- `python test/get_related_artists.py`
  - 特定アーティスト ID の関連アーティストを取得するデモ
  - ファイル冒頭の `artist_id` を必要に応じて変更

- `python test/gemini_artist_details.py "Artist Name"`
  - Gemini を使ってアーティストの詳細（概要/ジャンル/類似/出典など）を取得
  - 事前に `GEMINI_API_KEY` もしくは `GOOGLE_API_KEY` を `.env` に設定

- `python test/gemini_artist_research.py "アーティスト名"`
  - 本要件向け（活動歴/活動拠点/YouTube音源/音楽性/情報源URL）でJSONを返す
  - 例: `python test/gemini_artist_research.py "scorch away"`

- `python test/gemini_enrich_artists.py [--limit 10] [--save]`
  - Supabaseの`artists`から取得し、Geminiで詳細を付与
  - `--save` を付けると `artist_profiles` テーブルに upsert（事前にテーブル作成が必要）
  - `.env`: `supabase_url`, `supabase_service_key`, `GEMINI_API_KEY`（または`GOOGLE_API_KEY`）
  - 任意の環境変数: `ARTIST_LIMIT`, `GEMINI_SLEEP_SEC`, `PROFILES_UPSERT_CHUNK`

## Pytest の実行

開発依存（pytest）を入れていれば `test/` のテストを実行できます。

例:
- モジュール単位で実行: `pytest -q test/test_era_scraper.py`
- キーワードで絞り込み: `pytest -q -k era_scraper test/`
- `test/` 全体を実行: `pytest -q test/`

注意:
- 多くのテストが外部サービス（Spotify API、会場サイト）にアクセスします。ネットワーク負荷やレート制限に留意してください。
- `.env` が未設定/不十分な場合、資格情報が必要なテストは失敗/スキップされます。

## 主な環境変数

- Spotify: `spotify_client_id`, `spotify_client_secret`, `market`（既定 `JP`）, `limit`（既定 `50`）
- Supabase: `supabase_url`, `supabase_key`, `supabase_service_key`
- Database: `database_url`（PostgreSQL URL。未設定時はローカル SQLite `./test.db`）

これらは `packages.common.settings.Settings`（`pydantic-settings`）および `packages.common.db` から読み込まれます。

## トラブルシューティング

- `apps.*` や `packages.*` のインポートエラー:
  - プロジェクトルートで実行しているか確認
  - 仮想環境を有効化し、`pip install -e .` でパッケージをインストール

- Spotify の 401/403 エラー:
  - `.env` の `spotify_client_id` / `spotify_client_secret` を再確認
  - ネットワーク制限等でトークン取得に失敗する場合があります

- スクレイピング失敗:
  - 先方サイトの HTML 変更やアクセス制限の可能性。時間を置いて再試行

- DB 接続エラー:
  - 正しい `database_url` を設定（例: `postgresql+psycopg://...`）。未設定なら SQLite にフォールバック

## 関連情報

- メイン UI 起動: `python main.py`（FastAPI UI を起動。必要に応じてバックグラウンドでスケジューラを開始）
- コアコード: `src/tunescout/` 配下
