#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import xml.etree.ElementTree as ET
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
import json
import os
import logging
import time
import sys

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kkj_search.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KKJSearchNotifier:
    def __init__(self, config_file='config.json'):
        """初期化"""
        self.config = self.load_config(config_file)
        self.api_url = "http://www.kkj.go.jp/api/"
        self.db_path = self.config['database']['path']
        self.init_database()
        
    def load_config(self, config_file):
        """設定ファイルの読み込み"""
        if not os.path.exists(config_file):
            # デフォルト設定を作成
            default_config = {
                "organization": "防衛省",
                "keywords": ["サイバー", "セキュリティ", "構築", "システム", "調査", "研究"],
                "database": {
                    "path": "kkj_search.db"
                },
                "smtp": {
                    "server": "smtp.example.com",
                    "port": 587,
                    "use_tls": True,
                    "username": "your_email@example.com",
                    "password": "your_password"
                },
                "notification": {
                    "from_email": "your_email@example.com",
                    "from_name": "官公需情報システム",
                    "to_emails": ["recipient@example.com"],
                    "subject": "【官公需】新規案件通知"
                }
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info(f"デフォルト設定ファイル {config_file} を作成しました。設定を編集してください。")
            sys.exit(1)
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def init_database(self):
        """データベースの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                project_name TEXT,
                organization_name TEXT,
                cft_issue_date TEXT,
                category TEXT,
                procedure_type TEXT,
                location TEXT,
                tender_submission_deadline TEXT,
                opening_tenders_event TEXT,
                period_end_time TEXT,
                external_document_uri TEXT,
                file_type TEXT,
                file_size INTEGER,
                search_keyword TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("データベースを初期化しました")
    
    def search_api(self, keyword):
        """APIで検索を実行"""
        params = {
            'Organization_Name': self.config['organization'],
            'Query': keyword,
            'Count': 100  # 最大100件取得
        }
        
        try:
            logger.info(f"検索実行: 機関名={self.config['organization']}, キーワード={keyword}")
            response = requests.get(self.api_url, params=params, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                logger.error(f"APIエラー: ステータスコード {response.status_code}")
                return None
                
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API通信エラー: {str(e)}")
            return None
    
    def parse_xml_results(self, xml_data, search_keyword):
        """XML結果をパース"""
        results = []
        
        try:
            root = ET.fromstring(xml_data)
            
            # エラーチェック
            error = root.find('Error')
            if error is not None:
                logger.error(f"APIエラー: {error.text}")
                return results
            
            search_results = root.find('SearchResults')
            if search_results is None:
                return results
                
            search_hits = search_results.find('SearchHits')
            if search_hits is not None:
                logger.info(f"検索ヒット数: {search_hits.text}")
            
            for result in search_results.findall('SearchResult'):
                data = {
                    'key': self.get_xml_value(result, 'Key'),
                    'project_name': self.get_xml_value(result, 'ProjectName'),
                    'organization_name': self.get_xml_value(result, 'OrganizationName'),
                    'cft_issue_date': self.get_xml_value(result, 'CftIssueDate'),
                    'category': self.get_xml_value(result, 'Category'),
                    'procedure_type': self.get_xml_value(result, 'ProcedureType'),
                    'location': self.get_xml_value(result, 'Location'),
                    'tender_submission_deadline': self.get_xml_value(result, 'TenderSubmissionDeadline'),
                    'opening_tenders_event': self.get_xml_value(result, 'OpeningTendersEvent'),
                    'period_end_time': self.get_xml_value(result, 'PeriodEndTime'),
                    'external_document_uri': self.get_xml_value(result, 'ExternalDocumentURI'),
                    'file_type': self.get_xml_value(result, 'FileType'),
                    'file_size': self.get_xml_value(result, 'FileSize', is_int=True),
                    'search_keyword': search_keyword
                }
                results.append(data)
                
        except ET.ParseError as e:
            logger.error(f"XMLパースエラー: {str(e)}")
            
        return results
    
    def get_xml_value(self, element, tag_name, is_int=False):
        """XML要素から値を取得"""
        tag = element.find(tag_name)
        if tag is not None and tag.text:
            if is_int:
                try:
                    return int(tag.text)
                except ValueError:
                    return None
            return tag.text
        return None
    
    def save_to_database(self, results):
        """検索結果をデータベースに保存"""
        new_items = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO search_results (
                        key, project_name, organization_name, cft_issue_date,
                        category, procedure_type, location, tender_submission_deadline,
                        opening_tenders_event, period_end_time, external_document_uri,
                        file_type, file_size, search_keyword
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result['key'], result['project_name'], result['organization_name'],
                    result['cft_issue_date'], result['category'], result['procedure_type'],
                    result['location'], result['tender_submission_deadline'],
                    result['opening_tenders_event'], result['period_end_time'],
                    result['external_document_uri'], result['file_type'],
                    result['file_size'], result['search_keyword']
                ))
                
                if cursor.rowcount > 0:
                    new_items.append(result)
                    
            except sqlite3.Error as e:
                logger.error(f"データベースエラー: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return new_items
    
    def send_notification(self, new_items):
        """新規案件をメール通知"""
        if not new_items:
            return
            
        smtp_config = self.config['smtp']
        notification_config = self.config['notification']
        
        # メール本文の作成
        now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        body = f"""
官公需情報検索システムより新規案件のお知らせです。

検索日時: {now}
機関名: {self.config['organization']}
新規案件数: {len(new_items)} 件

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 新規案件詳細
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for i, item in enumerate(new_items, 1):
            body += f"\n【案件 {i}】\n"
            body += f"件名: {item['project_name'] or '不明'}\n"
            body += f"機関名: {item['organization_name'] or '不明'}\n"
            body += f"カテゴリ: {item['category'] or '不明'}\n"
            body += f"公示種別: {item['procedure_type'] or '不明'}\n"
            body += f"公告日: {item['cft_issue_date'] or '不明'}\n"
            
            if item['tender_submission_deadline']:
                body += f"入札開始日: {item['tender_submission_deadline']}\n"
            if item['opening_tenders_event']:
                body += f"開札日: {item['opening_tenders_event']}\n"
            if item['period_end_time']:
                body += f"納入期限: {item['period_end_time']}\n"
            if item['location']:
                body += f"履行場所: {item['location']}\n"
                
            body += f"URL: {item['external_document_uri'] or '不明'}\n"
            body += f"検索キーワード: {item['search_keyword']}\n"
            body += f"─" * 40 + "\n"
        
        body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
このメールは自動送信です。
官公需情報ポータルサイト: http://www.kkj.go.jp/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # メール送信
        msg = MIMEMultipart()
        
        # 送信者名の設定
        from_name = notification_config.get('from_name', '')
        if from_name:
            msg['From'] = formataddr((from_name, notification_config['from_email']))
        else:
            msg['From'] = notification_config['from_email']
            
        msg['To'] = ', '.join(notification_config['to_emails'])
        msg['Subject'] = notification_config['subject']
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        try:
            if smtp_config['use_tls']:
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"メール通知を送信しました: {len(new_items)} 件")
            
        except Exception as e:
            logger.error(f"メール送信エラー: {str(e)}")
    
    def run(self):
        """メイン処理"""
        all_new_items = []
        
        for keyword in self.config['keywords']:
            logger.info(f"キーワード '{keyword}' で検索開始")
            
            # API検索
            xml_data = self.search_api(keyword)
            if not xml_data:
                continue
            
            # 結果をパース
            results = self.parse_xml_results(xml_data, keyword)
            logger.info(f"検索結果: {len(results)} 件")
            
            # データベースに保存
            new_items = self.save_to_database(results)
            logger.info(f"新規案件: {len(new_items)} 件")
            
            all_new_items.extend(new_items)
            
            # API負荷対策のため少し待機
            time.sleep(1)
        
        # 新規案件があればメール通知
        if all_new_items:
            self.send_notification(all_new_items)
        
        logger.info(f"処理完了: 全新規案件 {len(all_new_items)} 件")

if __name__ == "__main__":
    notifier = KKJSearchNotifier()
    notifier.run()