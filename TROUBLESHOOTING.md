# トラブルシューティングガイド

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
# 1. まずメールなしでテスト
python kkj_search.py --no-mail

# 2. データベースの内容を確認
sqlite3 kkj_search.db "SELECT COUNT(*) FROM search_results;"

# 3. 案件数を確認してからメール送信を有効化
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

### Q: 検索結果が多すぎる
A: APIの仕様上、1回の検索で最大100件までしか取得できません。より絞り込んだキーワードを使用することを推奨します。

### Q: cron実行時にエラーが出る
A: ラッパースクリプト（run_kkj_search.sh）を使用しているか確認してください。また、絶対パスが正しいか確認してください。

## サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：
- エラーメッセージの全文
- config.json（パスワード部分は除く）
- ログファイルの該当部分
- 実行環境（OS、Pythonバージョン）