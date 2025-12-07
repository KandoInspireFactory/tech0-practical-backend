from sqlalchemy import create_engine

import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv(override=True) # Explicitly override any existing env vars

# データベース接続情報
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

# MySQLのURL構築
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SSL証明書のパスを自動解決 (プロジェクトルートにあると仮定)
# このファイルのパス: .../backend/db_control/connect_MySQL.py
# 証明書の場所: .../backend/DigiCertGlobalRootG2.crt.pem
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSL_CA_PATH = os.path.join(BASE_DIR, 'DigiCertGlobalRootG2.crt.pem')



# エンジンの作成
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "ssl_ca": SSL_CA_PATH
    }
)