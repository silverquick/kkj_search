# SMTP接続エラー対処法

## エラーの症状

```
SMTPエラー: Connection unexpectedly closed: timed out
```

このエラーは、SMTPサーバーへの接続がタイムアウトしたことを示しています。

## 診断手順

### 1. SMTP接続診断ツールを実行

```bash
# 診断ツールを実行
python test_smtp_connection.py

# すべてのテストを実行
python test_smtp_connection.py --all
```

### 2. 基本的な確認事項

#### ネットワーク接続の確認

```bash
# SMTPサーバーへのping
ping smtp.gmail.com

# ポートの開放確認（telnetがインストールされている場合）
telnet smtp.gmail.com 587

# ncコマンドでの確認
nc -zv smtp.gmail.com 587
```

#### ファイアウォールの確認

```bash
# Ubuntu/Debianの場合
sudo ufw status

# iptablesの確認
sudo iptables -L -n | grep 587
```

## 一般的な解決方法

### 1. ポート番号の変更

**config.json** を編集して、別のポートを試してください：

#### Gmail - ポート465（SSL）を使用

```json
{
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 465,
    "use_ssl": true,
    "use_tls": false,
    "username": "your_email@gmail.com",
    "password": "your_app_password"
  }
}
```

#### Gmail - ポート587（デフォルト）

```json
{
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "username": "your_email@gmail.com",
    "password": "your_app_password"
  }
}
```

### 2. 異なるメールプロバイダの設定例

#### Outlook/Office 365

```json
{
  "smtp": {
    "server": "smtp.office365.com",
    "port": 587,
    "use_tls": true,
    "username": "your_email@outlook.com",
    "password": "your_password"
  }
}
```

#### Yahoo Mail

```json
{
  "smtp": {
    "server": "smtp.mail.yahoo.com",
    "port": 587,
    "use_tls": true,
    "username": "your_email@yahoo.com",
    "password": "your_app_password"
  }
}
```

#### 企業メールサーバー（例）

```json
{
  "smtp": {
    "server": "mail.company.com",
    "port": 25,
    "use_tls": false,
    "username": "username",
    "password": "password"
  }
}
```

### 3. プロキシ環境での対処

企業ネットワークなどプロキシ環境の場合：

```bash
# 環境変数の設定
export http_proxy=http://proxy.company.com:8080
export https_proxy=http://proxy.company.com:8080
export no_proxy=localhost,127.0.0.1

# スクリプトを実行
python kkj_search.py --test-mail
```

### 4. Gmailの場合の特別な設定

#### アプリパスワードの生成

1. [Googleアカウント設定](https://myaccount.google.com/security)にアクセス
2. 「2段階認証」を有効化
3. 「アプリパスワード」を選択
4. 「メール」と「その他（カスタム名）」を選択
5. 生成されたパスワードをconfig.jsonに設定

#### 「安全性の低いアプリ」の許可（非推奨）

アプリパスワードが使用できない場合の代替手段：
1. [Googleアカウント設定](https://myaccount.google.com/lesssecureapps)
2. 「安全性の低いアプリのアクセス」を有効化

### 5. ISPの制限を回避

一部のISPは標準的なSMTPポートをブロックしています。

#### 代替ポートの使用

```json
{
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 2525,  // 代替ポート
    "use_tls": true,
    "username": "your_email@gmail.com",
    "password": "your_app_password"
  }
}
```

#### VPNの使用

ISPの制限を回避するためにVPNを使用することも可能です。

## スクリプトの修正（SSL対応）

現在のスクリプトはSSL接続（ポート465）に対応しています。
config.jsonで以下のように設定してください：

```json
{
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 465,
    "use_ssl": true,      // SSL接続を有効化
    "use_tls": false,     // STARTTLSは無効化
    "username": "your_email@gmail.com",
    "password": "your_app_password"
  }
}
```

または、STARTTLS（ポート587）を使用する場合：

```json
{
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "use_ssl": false,     // SSLは無効化
    "use_tls": true,      // STARTTLSを有効化（デフォルト）
    "username": "your_email@gmail.com",
    "password": "your_app_password"
  }
}
```

## それでも解決しない場合

1. **ネットワーク管理者に確認**
   - 企業ネットワークの場合、SMTP送信が制限されている可能性
   - 必要なポートの開放を依頼

2. **別の送信方法を検討**
   - SendGridなどのメール送信サービスのAPI
   - 社内のメールリレーサーバー
   - AWS SESなどのクラウドサービス

3. **ローカルメールサーバーの使用**
   - Postfixなどをローカルに設定
   - リレー設定で外部SMTPサーバーに転送

## デバッグ情報の収集

問題が解決しない場合は、以下の情報を収集してください：

```bash
# システム情報
uname -a
cat /etc/os-release

# ネットワーク情報
ip addr
ip route
cat /etc/resolv.conf

# Python環境
python --version
pip list | grep -E "smtplib|ssl|socket"

# 詳細なデバッグログ
python -c "import smtplib; smtplib._debug = True" kkj_search.py --test-mail
```