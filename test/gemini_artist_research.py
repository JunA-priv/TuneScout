"""
Gemini を使って指定アーティスト（日本向け）の詳細調査を行い、
活動歴/活動拠点/YouTube音源/音楽性/情報源URLをJSONで出力します。

使い方:
  python test/gemini_artist_research.py "アーティスト名"

前提:
  - 環境変数 GEMINI_API_KEY または GOOGLE_API_KEY
"""
import json
import sys

from packages.common.gemini import GeminiClient


def main() -> None:
    if len(sys.argv) < 2:
        print("使い方: python test/gemini_artist_research.py 'アーティスト名'")
        sys.exit(1)

    name = sys.argv[1]
    client = GeminiClient()
    data = client.research_artist_jp(name)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

