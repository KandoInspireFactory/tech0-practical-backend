#!/bin/bash
echo "Starting startup script..."

# 依存関係のインストール
echo "Installing dependencies..."
pip install -r requirements.txt

# アプリケーションの起動
echo "Starting Gunicorn..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --timeout 600
