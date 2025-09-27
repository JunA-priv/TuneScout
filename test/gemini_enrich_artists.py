"""
Supabaseのartistsテーブルからアーティストを取得し、Geminiで詳細プロファイルを生成します。

使い方:
  python test/gemini_enrich_artists.py [--limit 10] [--save]

前提:
  - `.env` に Supabase 設定（`supabase_url`, `supabase_service_key` など）
  - `.env` または環境変数に Gemini の API キー（`GEMINI_API_KEY` または `GOOGLE_API_KEY`）

オプション:
  --limit N      取得するアーティスト数（既定: 10）
  --save         取得結果を Supabase の `artist_profiles` に upsert（テーブルは事前に作成してください）

補足:
  - 保存先テーブル例: artist_profiles (artist_id text PK, name text, history text, base text,
    youtube jsonb, style text, sources jsonb, last_updated date, raw jsonb, created_at/updated_at timestamp)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List

from packages.common.db import supabase, supabase_admin
from packages.common.gemini import GeminiClient


def is_truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def fetch_artists(limit: int = 10) -> List[Dict[str, Any]]:
    client = supabase_admin or supabase
    if not client:
        print("Supabaseクライアントが初期化されていません。.env の supabase_url / supabase_service_key を設定してください。")
        sys.exit(1)

    # updated_at のあるスキーマを想定。無い場合は name でソート
    try:
        res = (
            client.table("artists")
            .select("id,name,popularity,genres,updated_at")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception:
        res = (
            client.table("artists")
            .select("id,name,popularity,genres")
            .order("name")
            .limit(limit)
            .execute()
        )
    return res.data or []


def to_profile_row(artist: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "artist_id": artist.get("id"),
        "name": profile.get("name") or artist.get("name"),
        "history": profile.get("history") or profile.get("summary"),
        "base": profile.get("base") or profile.get("origin"),
        "youtube": profile.get("youtube", []),
        "style": profile.get("style") or profile.get("genres"),
        "sources": profile.get("sources", []),
        "last_updated": profile.get("last_updated"),
        "raw": profile,
    }


def upsert_profiles(rows: List[Dict[str, Any]], chunk: int = 200) -> int:
    client = supabase_admin or supabase
    if not client:
        print("Supabaseクライアントが未設定のため、保存をスキップします。")
        return 0

    total = 0
    for i in range(0, len(rows), chunk):
        part = rows[i : i + chunk]
        if not part:
            continue
        # artist_id を一意キーとして upsert
        client.table("artist_profiles").upsert(part, on_conflict="artist_id").execute()
        total += len(part)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Geminiでアーティスト詳細を付与")
    parser.add_argument("--limit", type=int, default=int(os.getenv("ARTIST_LIMIT", "10")), help="取得する件数")
    parser.add_argument("--save", action="store_true", help="Supabaseに保存する")
    args = parser.parse_args()

    items = fetch_artists(limit=args.limit)
    if not items:
        print("アーティストが取得できませんでした。")
        return

    client = GeminiClient()
    sleep_sec = float(os.getenv("GEMINI_SLEEP_SEC", "1.0"))

    out_rows: List[Dict[str, Any]] = []
    for idx, ar in enumerate(items, 1):
        name = ar.get("name")
        print(f"[{idx}/{len(items)}] Gemini検索: {name}")
        try:
            prof = client.research_artist_jp(name)
        except Exception as e:
            print(f"  エラー: {e}")
            continue

        row = to_profile_row(ar, prof)
        out_rows.append(row)
        # 標準出力にもJSONを表示
        print(json.dumps(row, ensure_ascii=False, indent=2))

        if sleep_sec > 0:
            time.sleep(sleep_sec)

    if args.save and out_rows:
        saved = upsert_profiles(out_rows, chunk=int(os.getenv("PROFILES_UPSERT_CHUNK", "200")))
        print(f"Supabaseへ {saved} 件のプロフィールを保存済み")
    else:
        print("保存は行っていません（--save を付与で保存）")


if __name__ == "__main__":
    main()

