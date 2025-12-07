#!/bin/bash
echo "Starting startup script..."

# カレントディレクトリを表示
pwd
ls -la

# 依存関係のインストール
echo "Installing dependencies..."
pip install -r requirements.txt

# アプリケーションの起動
echo "Starting Gunicorn on port 8000..."
# exec を使うことで、シェルプロセスをgunicornプロセスに置き換え、シグナル処理を正しく行わせる
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000 --timeout 600