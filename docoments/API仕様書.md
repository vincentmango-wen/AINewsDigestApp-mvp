# API仕様書

不足情報:
- ベースURLのホスト名、ポート番号未記載
- APIバージョニングのURI運用方針未記載
- CORS許可オリジン未記載
- 将来公開時のRate Limit要件未記載
- 一覧APIのページング要件未記載
- 認証方式はMVPで不要と記載されているが、将来公開時の認証方式未記載
- 目標応答速度、可用性SLA、ログ保持期間未記載

合理的仮定:
- FastAPIのOpenAPI生成を前提に、MVP APIのベースパスは `/api/v1` とする
- ローカル検証用途のため、対象環境は `開発` と `将来の本番参考` を併記する
- 認証・認可はMVPでは未実装とし、すべて `不要` とする
- 一覧APIはMVPでは存在しないため、一覧API共通仕様は将来拡張向けの標準案として定義する
- 手動実行手段はHTTP APIのみとする

## 1. ドキュメント概要

|項目|内容|
|---|---|
|システム名|FocusDigest|
|APIバージョン|v1|
|作成日|2026-04-18|
|対象環境|開発 / 将来の本番参考|
|ベースURL|開発: `http://localhost:{port}/api/v1`、本番: 要確認|
|設計方針|RESTful API、FastAPIのOpenAPI前提、MVPではローカル実行確認用途に限定、命名規則は snake_case と複数形名詞を採用|

---

## 2. 認証・認可仕様

|項目|内容|
|---|---|
|認証方式|なし|
|認可方式|なし|
|トークン期限|該当なし|
|リフレッシュ有無|なし|

Gmail SMTP前提:
- `SMTP_HOST=smtp.gmail.com`
- `SMTP_PORT=587`
- `SMTP_USERNAME` はGmailアドレス
- `SMTP_PASSWORD` はGmailのアプリパスワード

補足:
- 基本設計書で「MVPでは外部公開を前提としない」「認証は導入しない」と明記されているため、全APIは認証不要とする
- 将来外部公開する場合は、認証方式を別途再設計する

---

## 3. 共通レスポンス形式

### 成功

```json
{
  "success": true,
  "data": {},
  "message": "成功"
}
```

### 失敗

```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "入力値が不正です"
}
```

### 共通ルール

|項目|内容|
|---|---|
|success|処理成功時は `true`、失敗時は `false` |
|data|成功時の返却データ。データがない場合は空オブジェクト `{}` |
|message|利用者または運用者が読める短い説明文 |
|error_code|失敗時のみ返却。アプリケーション側の分類コード |

### エラーコード一覧

|error_code|意味|
|---|---|
|VALIDATION_ERROR|入力値不正|
|CONFIGURATION_ERROR|必須設定不足|
|NOT_FOUND|対象データなし|
|JOB_ALREADY_RUNNING|同時実行禁止に抵触|
|EXTERNAL_API_ERROR|NewsAPI または OpenAI API 呼び出し失敗|
|MAIL_SEND_ERROR|SMTP送信失敗|
|INTERNAL_SERVER_ERROR|サーバー内部エラー|

---

## 4. API一覧

|機能|Method|Path|概要|認証|
|---|---|---|---|---|
|ヘルスチェック|GET|/api/v1/health|アプリケーション稼働確認|不要|
|ダイジェスト手動実行|POST|/api/v1/jobs/digest/run|ニュース取得からメール送信までを即時実行|不要|
|最新実行結果取得|GET|/api/v1/jobs/digest/runs/latest|直近の実行結果を取得|不要|

---

## 5. API詳細仕様

---

### API名：ヘルスチェック

#### 基本情報

|項目|内容|
|---|---|
|Method|GET|
|URL|/api/v1/health|
|概要|アプリケーションの起動状態を返す|
|認証|不要|

#### Query Parameters

なし

#### Validation

なし

#### Response

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "app_name": "FocusDigest",
    "timestamp": "2026-04-18T08:00:00+09:00"
  },
  "message": "成功"
}
```

#### Status Code

|Code|意味|
|---|---|
|200|応答成功|
|500|内部エラー|

---

### API名：ダイジェスト手動実行

#### 基本情報

|項目|内容|
|---|---|
|Method|POST|
|URL|/api/v1/jobs/digest/run|
|概要|指定分野のニュース取得からメール送信までの一連処理を手動実行する|
|認証|不要|

#### Request Body

```json
{}
```

#### Validation

|項目|条件|
|---|---|
|request body|不要。空ボディまたは空JSONのみ許可|
|server configuration|分野設定、NewsAPIキー、OpenAI APIキー、SMTP設定が存在すること|

#### Response

```json
{
  "success": true,
  "data": {
    "run_id": 12,
    "triggered_by": "manual",
    "started_at": "2026-04-18T08:00:00+09:00",
    "finished_at": "2026-04-18T08:01:42+09:00",
    "fetched_count": 20,
    "selected_count": 5,
    "summarized_count": 4,
    "email_status": "success",
    "error_message": null
  },
  "message": "ダイジェスト処理が完了しました"
}
```

#### Status Code

|Code|意味|
|---|---|
|200|実行成功または処理完了レスポンス返却|
|400|設定不足、入力不正|
|409|既にジョブ実行中|
|500|実行失敗|

#### 業務ルール

|項目|内容|
|---|---|
|実行起点|`triggered_by` は常に `manual` |
|対象分野|リクエストでは受け取らず、サーバー設定値を使用する |
|同時実行|実行中ジョブがある場合は新規実行を拒否する |
|メール送信|要約成功記事が0件の場合は `email_status=skipped` を返す |
|手動実行手段|MVPではHTTP APIのみとする |

#### エラーレスポンス例

```json
{
  "success": false,
  "error_code": "CONFIGURATION_ERROR",
  "message": "必須設定が不足しています"
}
```

---

### API名：最新実行結果取得

#### 基本情報

|項目|内容|
|---|---|
|Method|GET|
|URL|/api/v1/jobs/digest/runs/latest|
|概要|最新1件のダイジェスト実行結果を返す|
|認証|不要|

#### Query Parameters

なし

#### Validation

なし

#### Response

```json
{
  "success": true,
  "data": {
    "run_id": 12,
    "triggered_by": "scheduler",
    "started_at": "2026-04-18T08:00:00+09:00",
    "finished_at": "2026-04-18T08:01:42+09:00",
    "fetched_count": 20,
    "selected_count": 5,
    "summarized_count": 4,
    "email_status": "success",
    "error_message": null
  },
  "message": "成功"
}
```

#### Status Code

|Code|意味|
|---|---|
|200|取得成功|
|404|実行履歴が存在しない|
|500|内部エラー|

#### エラーレスポンス例

```json
{
  "success": false,
  "error_code": "NOT_FOUND",
  "message": "直近の実行履歴が存在しません"
}
```

---

## 6. 一覧API共通仕様

MVP時点では一覧APIは存在しない。

将来 `GET /api/v1/jobs/digest/runs` や記事一覧APIを追加する場合は、以下の共通仕様を適用する。

|項目|内容|
|---|---|
|page|1以上の整数。既定値は1|
|limit|1以上100以下の整数。既定値は20|
|sort|`created_at`, `published_at`, `started_at` など許可列のみ指定可|
|order|`asc` または `desc`|
|keyword|文字列検索条件。タイトル、配信元など対象列をAPIごとに限定する|

---

## 7. セキュリティ仕様

- HTTPS必須
  - 本番公開時に適用。MVPのローカル実行では対象外
- SQL Injection対策
  - ORMまたはプレースホルダ付きSQLを使用する
- XSS対策
  - APIはJSON返却のみとし、HTMLを返さない
- Rate Limit
  - MVPでは未実装。将来外部公開時に導入する
- CORS制御
  - MVPではローカル開発用オリジンのみ許可する方針とし、正式値は要確認
- ログイン試行制限
  - 認証未実装のため対象外
- 秘密情報管理
  - NewsAPIキー、OpenAI APIキー、SMTP資格情報、送信先アドレスは環境変数または `.env` で管理する

---

## 8. 非機能観点

|項目|内容|
|---|---|
|目標応答速度|要確認。MVPではローカル実行確認用途のため厳密なAPI応答SLOは設定しない|
|可用性|要確認。MVPでは常時稼働保証を行わない|
|監視|MVPではファイルログと `GET /api/v1/jobs/digest/runs/latest` による確認|
|ログ保持|要確認。MVPでは障害調査に必要な期間を保持|

補足:
- バッチ処理全体の完了目安は、基本設計に基づき「20件取得、5件要約、1通送信を数分以内」とする

---

## 9. 今後の拡張候補

- `GET /api/v1/jobs/digest/runs` の一覧API追加
- 分野設定変更API追加
- 複数配信先管理API追加
- 認証付き公開APIへの移行
- API v2での認証、監査項目、一覧検索強化
- 外部公開APIと管理者APIの分離
