#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMTP接続診断ツール
config.jsonの設定を使用してSMTP接続をテストします
"""

import json
import smtplib
import socket
import ssl
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

def load_config(config_file='config.json'):
    """設定ファイルの読み込み"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"エラー: {config_file} が見つかりません")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"エラー: {config_file} の解析に失敗しました: {e}")
        sys.exit(1)

def test_smtp_connection(config):
    """SMTP接続のテスト"""
    smtp_config = config['smtp']
    notification_config = config['notification']
    
    print("=== SMTP接続診断 ===")
    print(f"サーバー: {smtp_config['server']}")
    print(f"ポート: {smtp_config['port']}")
    print(f"TLS: {'有効' if smtp_config.get('use_tls', True) else '無効'}")
    print(f"SSL: {'有効' if smtp_config.get('use_ssl', False) else '無効'}")
    print(f"ユーザー: {smtp_config['username']}")
    print()
    
    # 1. DNS解決テスト
    print("1. DNS解決テスト...")
    try:
        ip_address = socket.gethostbyname(smtp_config['server'])
        print(f"   ✓ ホスト名を解決しました: {smtp_config['server']} -> {ip_address}")
    except socket.gaierror as e:
        print(f"   ✗ DNS解決に失敗しました: {e}")
        return False
    
    # 2. ポート接続テスト
    print(f"\n2. ポート接続テスト (ポート {smtp_config['port']})...")
    try:
        with socket.create_connection((smtp_config['server'], smtp_config['port']), timeout=10) as sock:
            print(f"   ✓ ポート {smtp_config['port']} に接続できました")
    except (socket.timeout, socket.error) as e:
        print(f"   ✗ ポート接続に失敗しました: {e}")
        return False
    
    # 3. SMTP接続テスト
    print("\n3. SMTP接続テスト...")
    try:
        if smtp_config.get('use_ssl', False):
            # SSL接続（ポート465用）
            print("   SSL接続を使用します")
            server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'], timeout=30)
        else:
            # 通常接続
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=30)
            
        print(f"   ✓ SMTPサーバーに接続しました")
        
        # EHLOコマンドテスト
        server.ehlo()
        print("   ✓ EHLOコマンドが成功しました")
        
        # TLSのテスト
        if smtp_config.get('use_tls', True) and not smtp_config.get('use_ssl', False):
            print("\n4. TLS接続テスト...")
            if server.has_extn('STARTTLS'):
                server.starttls()
                server.ehlo()  # TLS後に再度EHLO
                print("   ✓ STARTTLS接続が成功しました")
            else:
                print("   ✗ サーバーがSTARTTLSをサポートしていません")
                return False
        
        # 4. 認証テスト
        print("\n5. SMTP認証テスト...")
        try:
            server.login(smtp_config['username'], smtp_config['password'])
            print("   ✓ SMTP認証に成功しました")
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ✗ SMTP認証に失敗しました: {e}")
            print("   ユーザー名またはパスワードを確認してください")
            server.quit()
            return False
        except smtplib.SMTPException as e:
            print(f"   ✗ SMTP認証エラー: {e}")
            server.quit()
            return False
        
        # 5. テストメール送信（オプション）
        response = input("\nテストメールを送信しますか？ (y/N): ")
        if response.lower() == 'y':
            print("\n6. テストメール送信...")
            try:
                # メッセージの作成
                msg = MIMEMultipart()
                msg['From'] = formataddr((notification_config.get('from_name', ''), 
                                        notification_config['from_email']))
                msg['To'] = ', '.join(notification_config['to_emails'])
                msg['Subject'] = '【テスト】SMTP接続診断'
                
                body = """これはSMTP接続診断ツールによるテストメールです。

このメールが届いていれば、SMTP設定は正しく構成されています。

設定情報:
- SMTPサーバー: {}:{}
- TLS: {}
- 送信元: {}
- 送信先: {}

このメールは自動生成されました。
""".format(
                    smtp_config['server'], 
                    smtp_config['port'],
                    '有効' if smtp_config.get('use_tls', True) else '無効',
                    notification_config['from_email'],
                    ', '.join(notification_config['to_emails'])
                )
                
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # メール送信
                server.send_message(msg)
                print("   ✓ テストメールを送信しました")
                print(f"   送信先: {', '.join(notification_config['to_emails'])}")
            except Exception as e:
                print(f"   ✗ テストメール送信に失敗しました: {e}")
        
        server.quit()
        print("\n✓ すべてのテストが成功しました！")
        return True
        
    except smtplib.SMTPConnectError as e:
        print(f"   ✗ SMTP接続エラー: {e}")
        return False
    except smtplib.SMTPServerDisconnected as e:
        print(f"   ✗ サーバーが切断されました: {e}")
        return False
    except socket.timeout:
        print("   ✗ 接続がタイムアウトしました")
        return False
    except Exception as e:
        print(f"   ✗ 予期しないエラー: {type(e).__name__} - {e}")
        return False

def print_recommendations():
    """トラブルシューティングの推奨事項を表示"""
    print("\n=== トラブルシューティング ===")
    print("1. ファイアウォールの確認:")
    print("   - 送信ポート（25, 465, 587）が開いているか確認")
    print("   - アウトバウンド接続が許可されているか確認")
    print()
    print("2. 認証情報の確認:")
    print("   - ユーザー名（メールアドレス）が正しいか")
    print("   - パスワードが正しいか")
    print("   - 2段階認証を使用している場合はアプリパスワードが必要")
    print()
    print("3. サーバー設定の確認:")
    print("   - SMTPサーバーのアドレスが正しいか")
    print("   - ポート番号が正しいか（587: TLS, 465: SSL, 25: 通常）")
    print("   - TLS/SSL設定が適切か")
    print()
    print("詳細は SMTP_TROUBLESHOOT.md を参照してください。")

if __name__ == "__main__":
    print("SMTP接続診断ツール v1.0")
    print("=" * 40)
    
    # 設定ファイルの読み込み
    config = load_config()
    
    # SMTP接続テスト
    success = test_smtp_connection(config)
    
    # 失敗した場合は推奨事項を表示
    if not success:
        print_recommendations()
    
    sys.exit(0 if success else 1)