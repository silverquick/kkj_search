#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions用の設定ファイル生成スクリプト
"""

import json
import os
import sys

def create_config():
    """環境変数から設定ファイルを生成"""
    
    # 環境変数の取得とバリデーション
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_username = os.environ.get('SMTP_USERNAME', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    email_from = os.environ.get('EMAIL_FROM', '')
    email_to = os.environ.get('EMAIL_TO', '')
    openai_api_key = os.environ.get('OPENAI_API_KEY', '')
    
    # メールアドレスのリスト化（カンマ区切り、空白除去）
    email_to_list = [email.strip() for email in email_to.split(',') if email.strip()]
    
    # 必須項目のチェック
    missing_vars = []
    if not smtp_username:
        missing_vars.append('SMTP_USERNAME')
    if not smtp_password:
        missing_vars.append('SMTP_PASSWORD')
    if not email_from:
        missing_vars.append('EMAIL_FROM')
    if not email_to_list:
        missing_vars.append('EMAIL_TO')
    if not openai_api_key:
        missing_vars.append('OPENAI_API_KEY')
    
    if missing_vars:
        print(f"警告: 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        print("config.json.template を使用してデフォルト設定を作成します。")
    
    # 設定の構築
    config = {
        'smtp': {
            'server': smtp_server,
            'port': smtp_port,
            'username': smtp_username,
            'password': smtp_password,
            'use_tls': True
        },
        'email': {
            'from': email_from,
            'to': email_to_list,
            'subject': 'KKJ新着案件情報 - {date}'
        },
        'search': {
            'keywords': os.environ.get('SEARCH_KEYWORDS', 'システム開発,アプリケーション開発,ソフトウェア開発').split(','),
            'exclude_keywords': os.environ.get('EXCLUDE_KEYWORDS', '工事,建設,建築').split(','),
            'max_results': int(os.environ.get('MAX_RESULTS', '50'))
        },
        'openai': {
            'api_key': openai_api_key,
            'model': os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            'max_tokens': int(os.environ.get('OPENAI_MAX_TOKENS', '500'))
        },
        'database': {
            'path': 'kkj_search.db'
        }
    }
    
    # 設定ファイルの保存
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("config.json を作成しました。")
    
    # バリデーション結果を返す
    return len(missing_vars) == 0

if __name__ == '__main__':
    success = create_config()
    sys.exit(0 if success else 1)