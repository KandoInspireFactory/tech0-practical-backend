# Azure App Service バックエンドデプロイ障害と解決の記録 (2025-12-07)

## 1. 概要
Azure App Service (Linux) + Python (FastAPI) 環境へのデプロイにおいて、アプリケーションが起動せず `ModuleNotFoundError` や `Startup Probe Failed` が発生。
GitHub Actionsによるデプロイプロセスとディレクトリ構造の不整合が主な原因であったため、スタートアップコマンド内でGitクローンと環境構築を完結させる手法により解決した。

## 2. 発生していた問題と原因

### 2.1. `ModuleNotFoundError: No module named 'uvicorn'`
*   **症状:** Gunicorn起動時にUvicornが見つからずクラッシュ。
*   **原因:** Azure App Service (Oryx) の自動ビルドプロセスにおいて、`requirements.txt` が正しく認識されなかった、またはインストール先が実行環境と異なっていたため、依存パッケージがインストールされていなかった。
*   **背景:** GitHubリポジトリのルートではなく `backend/` ディレクトリ内にソースコードがあったが、デプロイ時のルートディレクトリ設定と不整合があった。

### 2.2. `Site startup probe failed` (タイムアウト)
*   **症状:** コンテナ起動後、230秒経過してもヘルスチェックが通らず、Azureにより強制再起動される。
*   **原因:**
    1.  スタートアップスクリプト内での `pip install` に時間がかかりすぎた。
    2.  GunicornがAzureの期待するポート (8000) で正しくリッスンできていなかった可能性。

### 2.3. `sh: 0: cannot open startup.sh: No such file`
*   **症状:** スタートアップコマンドで指定したスクリプトが見つからない。
*   **原因:** GitHub Actionsのデプロイ設定ミスにより、`startup.sh` が `/home/site/wwwroot/` に配置されていなかった。

### 2.4. `git: not found`
*   **症状:** 救済策としてスタートアップコマンドに `git clone` を記述したが失敗。
*   **原因:** Azure App ServiceのPython標準コンテナイメージには `git` コマンドがプリインストールされていなかった。

### 2.5. データベース接続エラー (SSL証明書)
*   **症状:** `FileNotFoundError` (SSL証明書が見つからない)。
*   **原因:** GitHubリポジトリ上に `DigiCertGlobalRootG2.crt.pem` がコミットされておらず、クローンした環境に証明書が存在しなかった。また、コード内のパス解決ロジックと環境変数の競合も一因。

---

## 3. 解決策と最終設定

### 3.1. スタートアップコマンドによる強制環境構築
Azureの標準デプロイ（Zipデプロイ）に依存せず、コンテナ起動時にGitHubから最新コードを取得し、その場で環境を構築する手法を採用。

**最終的なスタートアップコマンド:**
```bash
apt-get update && apt-get install -y git && rm -rf /tmp/repo && git clone https://github.com/KandoInspireFactory/tech0-practical-backend.git /tmp/repo && cd /tmp/repo && pip install -r requirements.txt && exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000 --timeout 600
```

**コマンドの解説:**
1.  `apt-get update && apt-get install -y git`: 不足していた `git` コマンドをインストール。
2.  `rm -rf /tmp/repo && git clone ...`: 既存の一時ディレクトリを消去し、最新のコードを `/tmp/repo` にクローン。
3.  `cd /tmp/repo`: クローンしたリポジトリのルート（`requirements.txt` や `app.py` がある場所）へ移動。
4.  `pip install -r requirements.txt`: 依存パッケージを確実にインストール。
5.  `exec gunicorn ...`: Gunicornをメインプロセスとして起動し、ポート8000で待機。

### 3.2. タイムアウト時間の延長
初期構築（apt-get, pip install）に時間がかかるため、Azureのコンテナ起動待ち時間を延長。

*   **アプリケーション設定名:** `WEBSITES_CONTAINER_START_TIME_LIMIT`
*   **値:** `1800` (30分)

### 3.3. コードの修正
*   **`backend/db_control/connect_MySQL.py`:** `SSL_CA_PATH` の環境変数による上書きロジックを削除し、常に相対パスから動的に解決するように変更。
*   **`backend/app.py`:** DB接続エラー時に詳細なトレースバックを出力するように変更。

---

## 4. 今後のための推奨事項

現在の設定は「とにかく動かす」ための強力な構成ですが、本番運用として最適化する余地があります。

1.  **GitHub Actions ワークフローの適正化:**
    *   ディレクトリ構造の問題を根本から解決し、`backend/` の中身だけをきれいにAzureのルート (`/home/site/wwwroot`) に展開できるように `.yml` を修正する。
2.  **Dockerイメージ化:**
    *   `Dockerfile` を作成し、ビルド済みのDockerイメージをAzure Container Registry経由でデプロイする。これにより、起動時の `pip install` や `git install` が不要になり、起動が数秒で完了するようになる。
3.  **SSL証明書の管理:**
    *   証明書ファイルをGitHubリポジトリに含めるか、Azure Key Vaultなどのセキュアな場所に保管し、環境変数経由で読み込むようにする。

## 5. 結論
バックエンドアプリケーションは現在、正常に稼働しており、ブラウザからのアクセス (`{"message":"FastAPI top page!"}`) およびデータベース接続に成功している。
