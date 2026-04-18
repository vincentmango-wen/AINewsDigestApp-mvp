# FocusDigest

FocusDigest は、指定した分野のニュースを取得し、AI で要約してメール配信することを目的とした MVP バックエンドです。  
外部 API 連携、SQLite 保存、定期実行、メール通知を一連で実装し、ポートフォリオとして説明しやすい構成を目指しています。

## 概要

- ニュース取得元: NewsAPI
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
  ├─ NewsAPI
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
- 現時点ではコードの多くが雛形段階で、設計書が先行しています

## 現状ステータス

2026-04-18 時点では、リポジトリは主に設計資料と Python パッケージ雛形で構成されています。

実装済み:

- ディレクトリ構成
- 依存ライブラリ定義
- 各モジュールのプレースホルダファイル
- 設計書、要件定義、API 仕様、DB 設計、実装手順書

未実装または未着手:

- FastAPI エンドポイント本体
- 設定読み込み
- DB 初期化
- NewsAPI / OpenAI / SMTP クライアント
- 業務サービス
- スケジューラ実処理
- テストコード
- Dockerfile
- `.env.example`

## 必要な環境変数

設計資料上、以下の設定を利用する前提です。

```env
CATEGORY=AI
NEWS_API_KEY=your_newsapi_key
OPENAI_API_KEY=your_openai_api_key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail_address
SMTP_PASSWORD=your_app_password
```

補足:

- `CATEGORY` は 2 文字以上 50 文字以内を想定
- SMTP は Gmail 前提で設計されています
- 現在は `.env.example` が未作成です

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

アプリ本体はまだ未実装のため、現時点ではそのまま起動しても API やバッチ処理は動作しません。  
今後の想定実行方法は以下です。

```bash
uvicorn app.main:app --reload
```

想定される確認ポイント:

- `GET /api/v1/health`
- `POST /api/v1/jobs/digest/run`
- `GET /api/v1/jobs/digest/runs/latest`

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

## 次に着手すべき項目

優先度順の候補:

1. `app/core/config.py` の設定管理実装
2. `app/db/connection.py` と `app/db/schema.sql` の DB 初期化実装
3. 外部 API / SMTP クライアント実装
4. サービス層実装
5. FastAPI エンドポイント実装
6. APScheduler 連携
7. テスト追加
8. Dockerfile と `.env.example` 追加
