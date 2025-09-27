# Spotify Artist Processor

スクレイピングで取得したアーティストをSpotify APIで検索し、全パラメータを取得して日本のアーティスト判定を行い、条件に合致するアーティストをSupabaseに登録するモジュールです。

## 機能

- **Spotify API全パラメータ取得**: アーティスト詳細、アルバム、人気楽曲など
- **日本アーティスト判定**: ジャンル、ISRC、レーベル情報から推定
- **人気度フィルタリング**: 日本アーティストで人気度6-24のアーティストを抽出
- **Supabase自動登録**: 条件に合致するアーティストを自動保存

## 使用方法

### 1. 単体テスト

```bash
cd src/tunescout
python test_spotify_processor.py
```

### 2. 全スクレイパー実行

```bash
cd src/tunescout
python spotify_processor_main.py
```

### 3. プログラムから使用

```python
from tunescout.spotify_artist_processor import SpotifyArtistProcessor

processor = SpotifyArtistProcessor()

# アーティスト名のリストを処理
artist_names = ["Anorak", "yard rat", "TTNG"]
results = processor.process_scraped_artists(artist_names)

print(f"日本アーティスト: {results['japanese_found']}件")
print(f"Supabase保存: {results['saved_to_supabase']}件")
```

## 日本アーティスト判定ロジック

以下の要素を総合的に判定:

1. **ジャンル**: "japanese" や "japan" を含むジャンルタグ
2. **ISRC**: 楽曲のISRCコードが "JP" で始まる
3. **レーベル**: 日本の音楽レーベルのヒント文字列

判定結果:
- `is_japanese: True` (confidence: high/medium)
- `is_japanese: False` (confidence: low)
- `is_japanese: None` (判定困難)

## 人気度フィルタ

- **対象**: `is_japanese: True` のアーティストのみ
- **範囲**: 人気度 6 ～ 24
- **目的**: マイナーだが一定の認知度があるアーティストを発掘

## 出力データ

Supabaseの `artists` テーブルに以下の形式で保存:

```json
{
  "id": "spotify_artist_id",
  "name": "アーティスト名",
  "spotify_id": "spotify_artist_id",
  "country": "JP",
  "popularity": 15,
  "followers": 1234,
  "genres": ["japanese indie", "shibuya-kei"],
  "external_urls": {"spotify": "https://..."}
}
```

## 設定

`.env` ファイルで以下を設定:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```