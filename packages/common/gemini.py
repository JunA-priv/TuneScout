import json
import os
import re
from typing import Any, Dict, Optional

import google.generativeai as genai

from .settings import settings


class GeminiClient:
    """Gemini クライアントの薄いラッパー。

    - `.env` から API キーとモデル名を自動読込（上書きも可）
    - JSONスキーマ的な出力を期待し、生成テキストからJSONを抽出
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        api_key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Gemini APIキーが未設定です（.env に GEMINI_API_KEY もしくは GOOGLE_API_KEY を設定してください）")

        genai.configure(api_key=api_key)
        self.model_name = model or settings.gemini_model or "gemini-1.5-flash"
        self.model = genai.GenerativeModel(self.model_name)

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        # コードフェンス ```json ... ``` を優先的に抽出
        m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
        if m:
            return json.loads(m.group(1))
        # それ以外は最初に現れる { ... } を緩く抽出
        m = re.search(r"(\{[\s\S]*\})", text)
        if m:
            return json.loads(m.group(1))
        # JSONが見つからない場合はテキストをそのまま返す
        return {"raw": text}

    def generate_artist_profile(self, name: str, lang: str = "ja") -> Dict[str, Any]:
        """アーティスト名から背景情報・概要・ジャンル・類似アーティスト等を生成してJSONで返す。"""
        sys_prompt = (
            "あなたは音楽リサーチャーです。信頼できる公開情報に基づき、簡潔で要点を押さえた日本語レポートを作成してください。"
        )
        user_prompt = f"""
次のアーティストについて日本語で要約レポートを作ってください。
アーティスト名: {name}

出力は必ずJSON（コードフェンス付き）で返してください。キーは以下:
{{
  "name": "アーティスト名",
  "summary": "200-400字程度の概要",
  "origin": "出身/拠点（分かれば）",
  "genres": ["ジャンル1", "ジャンル2"],
  "notable_works": ["代表作1", "代表作2"],
  "similar_artists": ["類似アーティストA", "類似アーティストB"],
  "sources": ["参考URL..."],
  "last_updated": "YYYY-MM-DD"
}}
"""
        # Gemini へ問い合わせ
        res = self.model.generate_content([
            {"role": "system", "parts": [sys_prompt]},
            {"role": "user", "parts": [user_prompt]},
        ])
        text = getattr(res, "text", None) or ""
        return self._extract_json(text)

    def research_artist_jp(self, name: str) -> Dict[str, Any]:
        """日本語向けの指定フォーマット（活動歴/拠点/YouTube音源/音楽性/情報源URL）で調査しJSON返却。"""
        sys_prompt = (
            "あなたは日本の音楽に特化した情報収集・推薦アシスタントです。"
            "指定アーティストについて信頼できる公開情報に基づき、簡潔で要点を押さえた回答を返してください。"
            "不明な項目は推測せず '不明' としてください。必ず出典URLを含めてください。"
        )

        user_prompt = f"""
指定アーティストの情報を以下のJSON形式（コードフェンス付き）で返してください。
アーティスト名: {name}

要件:
- 活動歴: 結成時期、メンバー構成、メジャー/インディーズ、主なリリース履歴
- 活動拠点: 主にライブを行っている地域・都市
- YouTube音源: 公式チャンネルURL、または公式音源・ライブのURL（最大5件）
- 音楽性: ジャンル、サウンドの特徴、影響源（分かればアーティスト名）
- sources: 参照したウェブページのURL一覧（必須）

出力JSONスキーマ例:
{{
  "name": "{name}",
  "history": "...",
  "base": "...",
  "youtube": ["https://...", "https://..."],
  "style": "...",
  "sources": ["https://...", "https://..."]
}}
"""

        res = self.model.generate_content([
            {"role": "system", "parts": [sys_prompt]},
            {"role": "user", "parts": [user_prompt]},
        ])
        text = getattr(res, "text", None) or ""
        return self._extract_json(text)

def get_gemini_client() -> GeminiClient:
    """Geminiクライアントを取得"""
    return GeminiClient()