# FocusDigest

FocusDigest は、指定した分野のニュースを取得し、AI で要約してメール配信することを目的とした MVP バックエンドです。  
外部 API 連携、SQLite 保存、定期実行、メール通知を一連で実装し、ポートフォリオとして説明しやすい構成を目指しています。

## 概要

- ニュース取得元: TheNewsAPI
- 要約: OpenAI API
- 保存先: SQLite
- 通知: SMTP
- 定期実行: APScheduler
- アプリ基盤: FastAPI

想定フロー:

1. 指定カテゴリのニュースを取得する
2. 取得記事を SQLite に保存する
3. 新しい記事から上位 5 件を選定する
4. OpenAI API で日本語要約を生成する
5. 要約結果を 1 通のメールにまとめて送信する
6. 毎日 08:00 に定期実行する

## MVP スコープ

含むもの:

- 単一カテゴリのニュース収集
- 記事保存と重複防止
- 上位記事の選定
- AI 要約
- メール送信
- 手動実行 API
- 実行履歴管理
- 日次スケジューリング

含まないもの:

- Web UI
- 認証、認可
- 複数ユーザー対応
- 複数配信先管理
- HTML メール
- クラウド本番運用
- 監視基盤、CI/CD

## 予定アーキテクチャ

```text
FastAPI
  ├─ API
  │   ├─ GET  /api/v1/health
  │   ├─ POST /api/v1/jobs/digest/run
  │   └─ GET  /api/v1/jobs/digest/runs/latest
  ├─ APScheduler
  ├─ Services
  ├─ Repositories
  ├─ SQLite (data/app.db)
  ├─ TheNewsAPI
  ├─ OpenAI API
  └─ SMTP
```

## ディレクトリ構成

```text
app/
  api/
  clients/
  core/
  db/
  repositories/
  schedulers/
  schemas/
  services/
tests/
docoments/
requirements.txt
requirements-dev.txt
```

補足:

- 設計資料ディレクトリ名は `documents` ではなく `docoments` です
- 実行手順の詳細は [起動手順書.md](./起動手順書.md) にまとめています

## 必要な環境変数

以下の設定を利用します。

```env
CATEGORY=AI
THE_NEWS_API_TOKEN=your_thenewsapi_token
OPENAI_API_KEY=your_openai_api_key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail_address
SMTP_PASSWORD=your_app_password
MAIL_TO_ADDRESS=recipient@example.com
```

補足:

- `CATEGORY` は 2 文字以上 50 文字以内を想定
- SMTP は Gmail 前提で設計されています
- 互換性のため `NEWS_API_KEY` でも読み込めますが、新規設定は `THE_NEWS_API_TOKEN` を推奨します
- `MAIL_FROM_ADDRESS` は未指定時に `SMTP_USERNAME` が使われます
- `DB_PATH`、`LOG_PATH`、`FETCH_LIMIT`、`SELECTION_LIMIT`、`SCHEDULE_HOUR`、`SCHEDULE_MINUTE` は任意です

## セットアップ

依存関係のインストール:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

`requirements.txt` に含まれる主要ライブラリ:

- `fastapi`
- `uvicorn[standard]`
- `apscheduler`
- `httpx`
- `openai`
- `python-dotenv`

## 実行方法

ローカル起動:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Docker 起動:

```bash
docker build -t focusdigest:local .
docker run --rm \
  --env-file .env \
  -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  focusdigest:local
```

主要な確認ポイント:

- `GET /api/v1/health`
- `POST /api/v1/jobs/digest/run`
- `GET /api/v1/jobs/digest/runs/latest`

手動実行 API はボディなし、空ボディ、または空 JSON で呼び出せます。

## データ保存とログ

- SQLite: `data/app.db`
- ログ: `logs/app.log`

Docker 利用時は、設計上は以下のようなホストマウントを想定しています。

```text
./data:/app/data
./logs:/app/logs
```

## 関連ドキュメント

主要資料:

- `docoments/企画概要.md`
- `docoments/要件定義.md`
- `docoments/基本設計書.md`
- `docoments/詳細設計書.md`
- `docoments/アーキテクチャ設計書.md`
- `docoments/API仕様書.md`
- `docoments/データベース設計書.md`
- `docoments/実装手順書.md`
