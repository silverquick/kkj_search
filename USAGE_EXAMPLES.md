# 使用例とコマンドオプション

## コマンドラインオプション

```bash
python kkj_search.py [オプション]
```

### 利用可能なオプション

| オプション | 説明 | 使用例 |
|----------|------|--------|
| `--test-mail` | テストメールを送信（検索は実行しない） | `python kkj_search.py --test-mail` |
| `--no-mail` | メール送信をスキップ（検索のみ実行） | `python kkj_search.py --no-mail` |
| `--config FILE` | 設定ファイルを指定 | `python kkj_search.py --config config.prod.json` |
| `--help` | ヘルプを表示 | `python kkj_search.py --help` |

## メール通知の動作

### 新規案件がある場合
- 案件の詳細情報を含むメールを送信
- 最大表示件数は `max_items_per_mail` で制限

### 新規案件がない場合
- 「新規案件はありませんでした」という通知メールを送信
- 検索は実行されたが新規案件がなかったことを明示

### メール通知を無効化する場合
```bash
# 検索は実行するがメールは送信しない
python kkj_search.py --no-mail
```

## 典型的な使用シナリオ

### 1. 初期セットアップ時

```bash
# Step 1: メール設定の確認
python kkj_search.py --test-mail

# Step 2: 検索機能の確認（メールなし）
python kkj_search.py --no-mail

# Step 3: 通常実行
python kkj_search.py
```

### 2. 開発・テスト時

```bash
# テスト用設定ファイルで実行
python kkj_search.py --config config.test.json --no-mail

# 本番用設定でメールテスト
python kkj_search.py --config config.prod.json --test-mail
```

### 3. トラブルシューティング時

```bash
# メール送信に問題がある場合
python kkj_search.py --no-mail

# SMTP設定を変更後の確認
python kkj_search.py --test-mail

# ログを詳細に確認しながら実行
python kkj_search.py 2>&1 | tee debug.log
```

### 4. 定期実行（cron）

```bash
# crontabの設定例
# 毎日9時に実行（新規案件の有無に関わらず通知）
0 9 * * * /path/to/project/run_kkj_search.sh

# 平日17時に通常実行
0 17 * * 1-5 /path/to/project/run_kkj_search.sh

# メール通知なしで実行（ログ収集のみ）
0 * * * * cd /path/to/project && python kkj_search.py --no-mail >> hourly.log 2>&1
```

## 複数環境での運用

### 開発環境

```bash
# config.dev.json
{
  "organization": "テスト省",
  "keywords": ["テスト"],
  "notification": {
    "to_emails": ["dev-team@example.com"]
  }
}

# 実行
python kkj_search.py --config config.dev.json --no-mail
```

### ステージング環境

```bash
# config.staging.json
{
  "organization": "防衛省",
  "keywords": ["サイバー"],
  "notification": {
    "to_emails": ["staging@example.com"],
    "max_items_per_mail": 10
  }
}

# 実行
python kkj_search.py --config config.staging.json
```

### 本番環境

```bash
# config.prod.json
{
  "organization": "防衛省",
  "keywords": ["サイバー", "セキュリティ", "システム"],
  "notification": {
    "to_emails": ["team@example.com", "manager@example.com"]
  }
}

# 実行（ラッパースクリプト経由）
./run_kkj_search.sh
```

## データベース操作

### 検索結果の確認

```bash
# 最新10件を表示
sqlite3 kkj_search.db "SELECT project_name, cft_issue_date FROM search_results ORDER BY created_at DESC LIMIT 10;"

# キーワード別の統計
sqlite3 kkj_search.db "SELECT search_keyword, COUNT(*) FROM search_results GROUP BY search_keyword;"

# 特定期間の案件数
sqlite3 kkj_search.db "SELECT COUNT(*) FROM search_results WHERE created_at >= date('now', '-7 days');"
```

### メンテナンス操作

```bash
# 90日以前のデータを削除
python kkj_maintenance.py --delete-days 90

# データベース最適化
python kkj_maintenance.py --vacuum

# 統計情報表示
python kkj_maintenance.py --stats
```

## ログの確認

### リアルタイムログ監視

```bash
# アプリケーションログ
tail -f kkj_search.log

# cronログ
tail -f cron.log

# すべてのログを同時に監視
tail -f *.log
```

### エラーログの抽出

```bash
# エラーのみ表示
grep ERROR kkj_search.log

# 特定日のエラー
grep "2024-12-15.*ERROR" kkj_search.log

# メール関連のエラー
grep -i "smtp\|mail.*error" kkj_search.log
```

## パフォーマンス確認

```bash
# 実行時間の計測
time python kkj_search.py --no-mail

# メモリ使用量の確認
/usr/bin/time -v python kkj_search.py --no-mail

# プロファイリング
python -m cProfile -s cumulative kkj_search.py --no-mail > profile.txt
```