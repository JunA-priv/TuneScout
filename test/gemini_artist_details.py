"""
Gemini を使ってアーティスト詳細を取得するサンプルスクリプト。

使い方:
  python test/gemini_artist_details.py "Artist Name"

環境変数:
  - GEMINI_API_KEY または GOOGLE_API_KEY
  - 任意: GEMINI_MODEL（既定: gemini-1.5-flash）
"""
import sys

from packages.common.gemini import GeminiClient


def main() -> None:
    if len(sys.argv) < 2:
        print("使い方: python test/gemini_artist_details.py 'Artist Name'")
        sys.exit(1)

    name = sys.argv[1]
    client = GeminiClient()
    profile = client.generate_artist_profile(name)
    print(profile)


if __name__ == "__main__":
    main()

