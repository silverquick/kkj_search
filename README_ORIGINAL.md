# 官公需情報検索・通知システム

官公需情報ポータルサイトのAPIを使用して、防衛省の入札情報を検索し、新規案件をメール通知するシステムです。

## 機能

- 指定したキーワードで官公需情報を検索
- 検索結果をデータベースに保存
- 新規案件のみを抽出してメール通知
- キーワードは個別に検索（AND検索ではない）
- 設定ファイルで柔軟にカスタマイズ可能

## 環境構築

### 1. pyenvのインストール

```bash
# 依存パッケージのインストール
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev \
    liblzma-dev python3-openssl git

# pyenvのインストール
git clone https://github.com/pyenv/pyenv.git ~/.pyenv

# 環境変数の設定
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# pyenv-virtualenvのインストール
git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

# 設定の反映
source ~/.bashrc
```

### 2. Python環境の作成

```bash
# Python 3.11のインストール（バージョンは適宜変更可）
pyenv install 3.11.7

# プロジェクト用の仮想環境を作成
pyenv virtualenv 3.11.7 kkj-search

# プロジェクトディレクトリの作成
mkdir -p ~/projects/kkj_search
cd ~/projects/kkj_search

# このディレクトリで自動的に仮想環境を有効化
pyenv local kkj-search
```

### 3. 依存パッケージのインストール

```bash
# requirements.txtの作成
cat > requirements.txt << EOF
requests==2.31.0
EOF

# パッケージのインストール
pip install --upgrade pip
pip install -r requirements.txt
```

## セットアップ

### 1. ファイルの配置

```bash
# プロジェクトディレクトリにいることを確認
cd ~/projects/kkj_search

# スクリプトファイルを配置
# kkj_search.py
# kkj_maintenance.py
# config.json（初回実行時に自動生成）
# requirements.txt

# 実行権限の付与
chmod +x kkj_search.py kkj_maintenance.py
```

### 2. スクリプトの環境設定

各スクリプトの先頭行（shebang）を以下のように修正：

```python
#!/usr/bin/env python3
```

これにより、pyenvで設定された環境のPythonが使用されます。

### 3. 設定ファイルの編集

初回実行時に `config.json` が自動生成されます。

```bash
# 初回実行（設定ファイルが生成される）
python kkj_search.py

# 設定ファイルの編集
nano config.json
```

以下の項目を環境に合わせて編集してください：

#### キーワードの設定
```json
"keywords": [
  "サイバー",
  "セキュリティ",
  "構築",
  "システム",
  "調査",
  "研究",
  "ネットワーク",  // 追加例
  "情報"           // 追加例
]
```

#### SMTPサーバーの設定

**Gmail の場合：**
```json
"smtp": {
  "server": "smtp.gmail.com",
  "port": 587,
  "use_tls": true,
  "username": "your_email@gmail.com",
  "password": "your_app_password"  // 2段階認証を有効にしてアプリパスワードを使用
}
```

**その他のメールサーバーの場合：**
```json
"smtp": {
  "server": "mail.your-server.com",
  "port": 587,
  "use_tls": true,
  "username": "your_username",
  "password": "your_password"
}
```

#### 通知先の設定
```json
"notification": {
  "from_email": "sender@example.com",
  "from_name": "官公需情報システム",  // 送信者の表示名（オプション）
  "to_emails": [
    "recipient1@example.com",
    "recipient2@example.com"
  ],
  "subject": "【官公需】防衛省 新規案件通知"
}
```

### 4. 手動実行テスト

```bash
# プロジェクトディレクトリで実行
cd ~/projects/kkj_search
python kkj_search.py

# ログの確認
tail -f kkj_search.log
```

## 定期実行の設定（cron）

### cronで実行するためのラッパースクリプトを作成

```bash
# run_kkj_search.shの作成
cat > run_kkj_search.sh << 'EOF'
#!/bin/bash
# pyenv環境を読み込み
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# プロジェクトディレクトリに移動
cd ~/projects/kkj_search

# スクリプトを実行
python kkj_search.py >> cron.log 2>&1
EOF

# 実行権限を付与
chmod +x run_kkj_search.sh
```

### crontabの設定

```bash
# crontabの編集
crontab -e

# 以下の行を追加（毎時0分に実行）
0 * * * * /home/username/projects/kkj_search/run_kkj_search.sh

# 1日3回（9時、13時、17時）に実行する場合
0 9,13,17 * * * /home/username/projects/kkj_search/run_kkj_search.sh

# メンテナンス（毎週日曜日の深夜2時に90日以前のデータを削除）
0 2 * * 0 cd /home/username/projects/kkj_search && /home/username/projects/kkj_search/run_kkj_maintenance.sh
```

### メンテナンス用ラッパースクリプト

```bash
# run_kkj_maintenance.shの作成
cat > run_kkj_maintenance.sh << 'EOF'
#!/bin/bash
# pyenv環境を読み込み
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# プロジェクトディレクトリに移動
cd ~/projects/kkj_search

# メンテナンススクリプトを実行
python kkj_maintenance.py --delete-days 90 --vacuum >> maintenance.log 2>&1
EOF

chmod +x run_kkj_maintenance.sh
```

## 環境の確認

```bash
# プロジェクトディレクトリで
cd ~/projects/kkj_search

# 現在のPython環境を確認
pyenv version

# インストールされているパッケージを確認
pip list

# Pythonのパスを確認
which python

# 環境変数の確認
python -c "import sys; print(sys.executable)"
```

## データベースの確認

```bash
# SQLiteクライアントのインストール（システムのパッケージマネージャを使用）
sudo apt install sqlite3

# データベースの確認
sqlite3 kkj_search.db

# テーブルの内容を表示
sqlite> SELECT * FROM search_results;

# 最新10件を表示
sqlite> SELECT project_name, cft_issue_date, search_keyword FROM search_results ORDER BY created_at DESC LIMIT 10;

# 終了
sqlite> .quit
```

## ログの確認

```bash
# ログファイルの確認
tail -f kkj_search.log

# cronログの確認
tail -f cron.log

# メンテナンスログの確認
tail -f maintenance.log
```

## トラブルシューティング

### pyenv関連の問題

1. pyenvコマンドが見つからない場合
```bash
source ~/.bashrc
```

2. Pythonのビルドに失敗する場合
```bash
# 依存パッケージを再確認
sudo apt install -y build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm
```

### メールが送信されない場合

1. SMTP設定を確認
   - サーバー名、ポート番号が正しいか
   - ユーザー名、パスワードが正しいか
   - TLS設定が適切か

2. Gmailの場合
   - 2段階認証を有効化
   - アプリパスワードを生成して使用
   - 「安全性の低いアプリのアクセス」を許可（非推奨）

3. ファイアウォール設定
   - 送信ポート（25, 587, 465など）が開いているか確認

### API検索でエラーが発生する場合

1. ネットワーク接続を確認
2. APIのURLが正しいか確認（http://www.kkj.go.jp/api/）
3. パラメーターの形式が正しいか確認

### データベースエラーが発生する場合

1. 書き込み権限を確認
```bash
ls -la kkj_search.db
chmod 664 kkj_search.db
```

2. ディスク容量を確認
```bash
df -h
```

## 開発環境の管理

### パッケージの更新

```bash
# プロジェクトディレクトリで
cd ~/projects/kkj_search

# パッケージの更新
pip install --upgrade -r requirements.txt

# 現在の環境をrequirements.txtに保存
pip freeze > requirements.txt
```

### 環境の削除

```bash
# 仮想環境の削除
pyenv uninstall kkj-search
```

### 環境の再作成

```bash
# 新しい環境を作成
pyenv virtualenv 3.11.7 kkj-search-new

# プロジェクトディレクトリで環境を切り替え
cd ~/projects/kkj_search
pyenv local kkj-search-new

# パッケージの再インストール
pip install -r requirements.txt
```

## カスタマイズ例

### 機関名を変更する場合

```json
"organization": "国土交通省"  // 防衛省から変更
```

### 検索件数を増やす場合

スクリプトの87行目付近を編集：
```python
'Count': 100  # 最大1000まで指定可能
```

### 複数の機関を検索する場合

config.jsonを拡張して、複数の機関を指定できるようにスクリプトを改修することも可能です。

## 注意事項

- 官公需情報ポータルサイトの利用規約に従ってください
- APIへの負荷を考慮し、適切な間隔で実行してください
- 個人情報や機密情報の取り扱いに注意してください
- 定期的にパッケージのセキュリティアップデートを確認してください

## ライセンス

本スクリプトは自由に使用・改変できますが、官公需情報ポータルサイトの利用規約に従う必要があります。