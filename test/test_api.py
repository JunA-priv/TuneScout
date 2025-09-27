#!/usr/bin/env python3
"""API動作テスト"""

import asyncio
import httpx
import time
import subprocess
import signal
import os

API_BASE_URL = "http://localhost:8000"

async def test_api_endpoints():
    """API エンドポイントテスト"""
    endpoints = [
        ("/", "ホームページ"),
        ("/health", "ヘルスチェック"),
        ("/dashboard", "ダッシュボード"),
        ("/test-supabase", "Supabaseテストページ"),
    ]
    
    async with httpx.AsyncClient() as client:
        for endpoint, description in endpoints:
            try:
                response = await client.get(f"{API_BASE_URL}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ {description} ({endpoint}): OK")
                else:
                    print(f"❌ {description} ({endpoint}): {response.status_code}")
            except Exception as e:
                print(f"❌ {description} ({endpoint}): エラー - {e}")

def start_api_server():
    """APIサーバーを起動"""
    print("APIサーバーを起動中...")
    process = subprocess.Popen([
        "uv", "run", "uvicorn", "apps.api.main:app", 
        "--host", "0.0.0.0", "--port", "8000"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # サーバー起動を待機
    time.sleep(3)
    return process

async def main():
    print("=== TuneScout API動作テスト ===\n")
    
    # APIサーバー起動
    server_process = start_api_server()
    
    try:
        # エンドポイントテスト
        await test_api_endpoints()
        
    finally:
        # サーバー停止
        print("\nAPIサーバーを停止中...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    asyncio.run(main())