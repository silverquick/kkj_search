# トラブルシューティングガイド

## 初期セットアップ時のメール設定確認

### メール送信機能のテスト手順

1. **まず設定ファイルを確認**
```bash
cat config.json | grep -A 10 smtp
```

2. **テストメールを送信**
```bash
python kkj_search.py --test-mail
```

3. **成功時のログ**
```
2024-12-15 10:30:00 - INFO - === テストメール送信モード ===
2024-12-15 10:30:00 - INFO - メール送信テストを開始します
2024-12-15 10:30:00 - INFO - テストメール送信を開始します
2024-12-15 10:30:01 - INFO - SMTPサーバーに接続しました
2024-12-15 10:30:01 - INFO - SMTPサーバーにログインしました
2024-12-15 10:30:02 - INFO - テストメールを送信しました
2024-12-15 10:30:02 - INFO - テストメールの送信に成功しました
2024-12-15 10:30:02 - INFO - === テストメール送信完了 ===
```

4. **受信メールの確認**
- 件名に【テスト】が付いているか
- ダミーの案件情報が含まれているか
- SMTP設定情報が記載されているか

## スクリプトが終了しない（ハングする）

### 症状
- 検索は完了するが、その後シェルに戻らない
- 最後のログが「新規案件: XX 件」で止まる

### 原因
- 大量の新規案件でメール送信処理が時間がかかっている
- SMTP接続でタイムアウトしている
- SMTP認証エラーが発生している

### 解決方法

1. **プロセスを強制終了**
```bash
# Ctrl+C で停止
# または別のターミナルから
ps aux | grep kkj_search
kill -9 [プロセスID]
```

2. **メール送信なしでテスト実行**
```bash
python kkj_search.py --no-mail
```

3. **config.jsonを修正**
```json
{
  "notification": {
    "max_items_per_mail": 20  // 少ない数に設定
  }
}
```

4. **ログを確認**
```bash
tail -f kkj_search.log
```

## 初回実行時の推奨手順

初回実行時は大量の案件がヒットする可能性があるため：

```bash
# 1. まずメール設定をテスト
python kkj_search.py --test-mail

# 2. メールなしで検索テスト
python kkj_search.py --no-mail

# 3. データベースの内容を確認
sqlite3 kkj_search.db "SELECT COUNT(*) FROM search_results;"

# 4. 案件数を確認してからメール送信を有効化
python kkj_search.py
```

## SMTP接続エラー

### Gmail使用時のエラー

**エラー例：**
```
SMTP認証エラー: ユーザー名またはパスワードが正しくありません
```

**解決方法：**
1. Googleアカウントで2段階認証を有効化
2. アプリパスワードを生成
3. config.jsonのpasswordにアプリパスワードを設定

**エラー例：**
```
SMTP接続エラー: サーバーに接続できません
```

**解決方法：**
1. ネットワーク接続を確認
2. ファイアウォールでポート587が開いているか確認
3. プロキシ設定を確認

## その他のSMTPサーバー

### Office 365
```json
{
  "smtp": {
    "server": "smtp.office365.com",
    "port": 587,
    "use_tls": true,
    "username": "your-email@company.com",
    "password": "your-password"
  }
}
```

### 自社メールサーバー
```json
{
  "smtp": {
    "server": "mail.company.local",
    "port": 25,
    "use_tls": false,
    "username": "username",
    "password": "password"
  }
}
```

## デバッグモード

詳細なログを確認する場合：

```python
# kkj_search.pyの先頭付近に追加
import logging
logging.basicConfig(level=logging.DEBUG)
```

## データベースのリセット

すべてのデータをリセットする場合：

```bash
# データベースファイルを削除
rm kkj_search.db

# 再実行（新しいデータベースが作成される）
python kkj_search.py --no-mail
```

## よくある質問

### Q: 毎回すべての案件が「新規」として検出される
A: データベースファイルが正しく保存されているか確認してください。
```bash
ls -la kkj_search.db
```

### Q: 特定のキーワードだけ検索したい
A: config.jsonのkeywordsを編集してください。
```json
{
  "keywords": ["サイバー"]  // 1つだけに絞る
}
```

### Q: 検索結果が少ない、または期待した案件が見つからない
A: 現在のシステムは**件名のみ**を検索対象としています。

1. より一般的なキーワードを試す
   - 「サイバーセキュリティ」→「サイバー」
   - 「ネットワーク構築」→「ネットワーク」または「構築」

2. 全文検索に変更する場合は、SEARCH_METHOD.mdを参照してください

3. キーワードの組み合わせ
   - 各キーワードは個別に検索されるため、関連するキーワードを複数登録

### Q: cron実行時にエラーが出る
A: ラッパースクリプト（run_kkj_search.sh）を使用しているか確認してください。また、絶対パスが正しいか確認してください。

## サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：
- エラーメッセージの全文
- config.json（パスワード部分は除く）
- ログファイルの該当部分
- 実行環境（OS、Pythonバージョン）