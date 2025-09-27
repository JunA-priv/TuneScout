# TuneScout - Music Discovery Recommendation System

音楽発掘レコメンドシステム。新人アーティストの発掘と日次レコメンド配信を行います。

## 特徴

- 🎵 Spotify APIを使用した新譜・新人アーティスト発掘
- 📧 日次メールレコメンド配信
- 🎯 人気度フィルタリング（マイナーアーティスト優先）
- 🌐 日本市場向け最適化
- 🔍 音楽メディア記事との連携

## 技術スタック

- **Backend**: FastAPI + SQLAlchemy + Supabase + pgvector
- **Frontend**: Jinja2 テンプレート
- **外部API**: Spotify Web API
- **メール**: SendGrid
- **認証**: Supabase Auth

## セットアップ（Ubuntu 開発環境）

1. Supabaseプロジェクト作成:
   - [Supabase](https://supabase.com)でプロジェクト作成
   - Database > Extensions で `vector` を有効化

2. 環境変数設定:
```bash
cp .env.example .env
# .envファイルを編集してSupabase URLとキーを設定
```

3. 依存関係インストール（ローカル Ubuntu）:
```bash
uv sync
```

4. 依存ミドルウェア（DB/Redis）をDockerで起動:
```bash
# APIはローカルで実行、DBとRedisだけDockerで起動
docker compose up -d db redis
```

5. データベースマイグレーション:
```bash
uv run alembic upgrade head
```

6. 開発サーバー起動（ホストのUbuntuで実行）:
```bash
uv run uvicorn apps.api.main:app --reload
```

補足: API も Docker コンテナでホットリロードしたい場合は以下。
```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build api
```

## API エンドポイント

- `GET /` - ホームページ
- `POST /auth/register` - ユーザー登録
- `POST /auth/login` - ログイン
- `POST /auth/logout` - ログアウト
- `GET /auth/me` - ユーザープロフィール
- `GET /recommendations/today` - 本日のレコメンド
- `GET /artists/{id}` - アーティスト詳細

## 開発

```bash
# 依存関係インストール
uv sync

# 開発サーバー起動
uv run uvicorn apps.api.main:app --reload

# マイグレーション作成
uv run alembic revision --autogenerate -m "description"

# マイグレーション実行
uv run alembic upgrade head
```

## 実行（Windows + Docker Desktop）

Windows では Docker Desktop 上でコンテナを実行することを想定しています。

- `compose.yaml` は本番寄り（コードのバインドマウント無し、イメージ内の依存関係を使用）
- 必要なら環境変数は `.env` または `compose.yaml` の `environment` を利用

```powershell
docker compose up --build -d

# ログ確認
docker compose logs -f api
```

開発用のホットリロードを有効にする場合は、`compose.dev.yaml` を併用してください（Ubuntu/WSL でも同様）。

```powershell
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

注意: Windows ホストでボリュームマウント（`.:/app`）を使うと、イメージビルド時に作成された仮想環境が隠蔽されます。上記のように本番寄り設定（バインドマウント無し）で実行することで、この問題を回避しています。

## Supabase設定

### 必要なExtensions
- `vector` - ベクトル検索用

### RLS (Row Level Security)
ユーザーデータのセキュリティのため、`user_profiles`テーブルにRLSを設定してください。
