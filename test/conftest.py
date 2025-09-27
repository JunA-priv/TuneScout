"""
Pytest 用の前処理: プロジェクトルートと src/ を import パスへ追加。

これにより test/ からの実行時でも `apps`, `packages`, `scrapers`, `tunescout` が
インポート可能になります。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

root_str = str(ROOT)
src_str = str(SRC)

if root_str not in sys.path:
    sys.path.insert(0, root_str)

if SRC.exists() and src_str not in sys.path:
    sys.path.insert(0, src_str)

