# 官公需情報検索・通知システム

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

官公需情報ポータルサイトのAPIを使用して、指定した機関の入札情報を定期的に検索し、新規案件をメール通知するシステムです。

## 特徴

- 🔍 キーワードベースの検索（件名に対して前後方・途中一致検索）
- 📧 新規案件のメール通知
- 💾 SQLiteデータベースによる履歴管理
- 🔄 定期実行対応（cron）
- 🐍 Python仮想環境による環境分離（pyenv）
- 📊 データベースメンテナンス機能
- 🌐 ChatGPT-4oによる案件概要生成（URLやPDFの内容を自動要約）

## 必要要件

- Ubuntu 20.04以降（他のLinuxディストリビューションでも動作可能）
- Python 3.11以降
- インターネット接続
- メール送信用のSMTPサーバー

## クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/YOUR_USERNAME/kkj-search-system.git
cd kkj-search-system
```

### 2. セットアップの実行

```bash
chmod +x setup.sh
./setup.sh
```

### 3. 設定ファイルの作成

```bash
# テンプレートから設定ファイルを作成
cp config.json.template config.json

# 設定を編集
nano config.json
```

### 4. テスト実行

```bash
cd ~/projects/kkj_search
python kkj_search.py
```

## 設定

`config.json`で以下の項目を設定できます：

- **organization**: 検索対象の機関名（例：防衛省）
- **keywords**: 検索キーワードのリスト
- **smtp**: メールサーバー設定
- **notification**: 通知先メールアドレス
- **openai**: ChatGPT API設定（任意）

設定例：
```json
{
  "organization": "防衛省",
  "keywords": ["サイバー", "セキュリティ", "システム"],
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "username": "your_email@gmail.com",
    "password": "your_app_password"
  },
  "openai": {
    "api_key": "YOUR_OPENAI_API_KEY",
    "model": "gpt-4o"
  }
}
```

## 使用方法

### 手動実行

```bash
python kkj_search.py
```

### 定期実行（cron）

```bash
# crontabを編集
crontab -e

# 毎時実行の例
0 * * * * /home/username/projects/kkj_search/run_kkj_search.sh
```

### データベースメンテナンス

```bash
# 90日以前のデータを削除
python kkj_maintenance.py --delete-days 90 --vacuum

# 統計情報の表示
python kkj_maintenance.py --stats
```

## ファイル構成

```
kkj-search-system/
├── kkj_search.py           # メイン検索スクリプト
├── kkj_maintenance.py      # メンテナンススクリプト
├── setup.sh                # セットアップスクリプト
├── requirements.txt        # Python依存パッケージ
├── config.json.template    # 設定ファイルテンプレート
├── run_kkj_search.sh       # cron実行用ラッパー
├── run_kkj_maintenance.sh  # メンテナンス用ラッパー
├── README.md               # ドキュメント
└── .gitignore             # Git除外設定
```

## API仕様

このシステムは[官公需情報ポータルサイト](http://www.kkj.go.jp/)のAPIを使用しています。

主な検索パラメータ：
- Project_Name: 件名での検索（前後方・途中一致）
- Organization_Name: 機関名での検索
- Count: 返却件数（最大1000）
- Category: カテゴリー（物品/工事/役務）

**注意**: 本システムでは、キーワードは件名（Project_Name）に対してのみ検索を行います。
全文検索が必要な場合は、コードの修正が必要です。

## トラブルシューティング

### pyenv関連
- `pyenv: command not found`: `source ~/.bashrc`を実行

### メール送信
- Gmailの場合：2段階認証とアプリパスワードを設定
- ファイアウォール：SMTPポート（587/465）を開放

### データベース
- 権限エラー：`chmod 664 kkj_search.db`

詳細は[README.md](README.md)を参照してください。

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずIssueを作成して変更内容を説明してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)を参照してください。

## 注意事項

- 官公需情報ポータルサイトの利用規約を遵守してください
- APIへの過度なアクセスは避けてください
- 取得したデータの取り扱いには注意してください

## 謝辞

- 官公需情報ポータルサイト（経済産業省）