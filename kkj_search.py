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
import tempfile
import openai

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
        self.openai_api_key = self.config.get('openai', {}).get('api_key')
        self.openai_model = self.config.get('openai', {}).get('model', 'gpt-4o')
        self.openai_client = None
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            try:
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            except Exception as e:
                logger.error(f"OpenAIクライアント初期化エラー: {e}")
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
                    "subject": "【官公需】新規案件通知",
                    "max_items_per_mail": 50
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
            'Project_Name': keyword,  # 件名での検索に変更
            'Count': 100  # 最大100件取得
        }
        
        try:
            logger.info(f"検索実行: 機関名={self.config['organization']}, 件名キーワード={keyword}")
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

    def summarize_url(self, url):
        """URLの内容をChatGPTで要約 (PDFにも対応)"""
        if not url or not self.openai_api_key or not self.openai_client:
            return None
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"要約用にURLを取得できません: {url}")
                return None

            content_type = response.headers.get("Content-Type", "").lower()
            is_pdf = "application/pdf" in content_type or url.lower().endswith(".pdf")

            if is_pdf:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name
                try:
                    upload = self.openai_client.files.create(
                        file=open(tmp_path, "rb"),
                        purpose="assistants",
                    )
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "以下のPDFの内容を日本語で100文字程度に要約してください。"},
                                {"type": "file", "file_id": upload.id},
                            ],
                        }
                    ]
                    result = self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=messages,
                        max_tokens=200,
                    )
                    return result.choices[0].message.content.strip()
                finally:
                    os.remove(tmp_path)
            else:
                text = response.text[:4000]
                prompt = (
                    "以下のHTMLの内容を日本語で100文字程度に要約してください。\n" + text
                )
                result = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                )
                return result.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"ChatGPT要約エラー: {e}")
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
        """新規案件をメール通知（案件がない場合も通知）"""
        smtp_config = self.config['smtp']
        notification_config = self.config['notification']
        
        # メール本文の作成
        now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        
        if not new_items:
            # 新規案件がない場合
            body = f"""
官公需情報検索システムより検索結果のお知らせです。

検索日時: {now}
機関名: {self.config['organization']}
検索キーワード: {', '.join(self.config['keywords'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 検索結果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

新規案件はありませんでした。

指定されたキーワードに該当する新しい入札案件は
見つかりませんでした。

※ 既に登録済みの案件は除外されています。
※ キーワードは件名に対してのみ検索されます。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
このメールは自動送信です。
官公需情報ポータルサイト: http://www.kkj.go.jp/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        else:
            # 新規案件がある場合
            # メール1通あたりの最大案件数を取得（デフォルト: 50件）
            max_items = notification_config.get('max_items_per_mail', 50)
            
            # 案件数が多い場合は制限
            if len(new_items) > max_items:
                logger.warning(f"新規案件が{len(new_items)}件と多いため、最初の{max_items}件のみ通知します")
                items_to_send = new_items[:max_items]
                remaining = len(new_items) - max_items
            else:
                items_to_send = new_items
                remaining = 0
            
            body = f"""
官公需情報検索システムより新規案件のお知らせです。

検索日時: {now}
機関名: {self.config['organization']}
新規案件数: {len(new_items)} 件"""

            if remaining > 0:
                body += f"\n※ 案件数が多いため、最初の{max_items}件のみ表示します。（残り{remaining}件）"
            else:
                body += f"\n表示案件数: {len(items_to_send)} 件"

            body += """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 新規案件詳細
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            for i, item in enumerate(items_to_send, 1):
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
                summary = self.summarize_url(item['external_document_uri'])
                if summary:
                    body += f"概要: {summary}\n"
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
            if new_items:
                logger.info(f"メール送信を開始します: 新規案件 {len(new_items)} 件")
            else:
                logger.info(f"メール送信を開始します: 新規案件なし（通知のみ）")
            
            # タイムアウトを設定（30秒）
            if smtp_config.get('use_ssl', False):
                # SSL接続（ポート465用）
                logger.info(f"SSL接続を使用: {smtp_config['server']}:{smtp_config['port']}")
                server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'], timeout=30)
            elif smtp_config.get('use_tls', True):
                # STARTTLS接続（ポート587用）
                logger.info(f"STARTTLS接続を使用: {smtp_config['server']}:{smtp_config['port']}")
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=30)
                server.starttls()
            else:
                # 非暗号化接続
                logger.info(f"非暗号化接続を使用: {smtp_config['server']}:{smtp_config['port']}")
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=30)
            
            logger.info("SMTPサーバーに接続しました")
            server.login(smtp_config['username'], smtp_config['password'])
            logger.info("SMTPサーバーにログインしました")
            
            server.send_message(msg)
            server.quit()
            
            if new_items:
                logger.info(f"メール通知を送信しました: 新規案件 {len(new_items)} 件")
            else:
                logger.info(f"メール通知を送信しました: 新規案件なし")
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP認証エラー: ユーザー名またはパスワードが正しくありません - {str(e)}")
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP接続エラー: サーバーに接続できません - {str(e)}")
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTPサーバー切断: {str(e)}")
        except socket.timeout as e:
            logger.error(f"接続タイムアウト: {str(e)}")
        except smtplib.SMTPException as e:
            logger.error(f"SMTPエラー: {str(e)}")
        except Exception as e:
            logger.error(f"メール送信エラー: {type(e).__name__} - {str(e)}")
            if smtp_config['use_tls']:
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=30)
            
            logger.info("SMTPサーバーに接続しました")
            server.login(smtp_config['username'], smtp_config['password'])
            logger.info("SMTPサーバーにログインしました")
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"メール通知を送信しました: {len(new_items)} 件")
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP認証エラー: ユーザー名またはパスワードが正しくありません - {str(e)}")
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP接続エラー: サーバーに接続できません - {str(e)}")
        except smtplib.SMTPException as e:
            logger.error(f"SMTPエラー: {str(e)}")
        except Exception as e:
            logger.error(f"メール送信エラー: {type(e).__name__} - {str(e)}")
    
    def run(self):
        """メイン処理"""
        all_new_items = []
        total_searched = 0
        
        for keyword in self.config['keywords']:
            logger.info(f"キーワード '{keyword}' で検索開始")
            
            # API検索
            xml_data = self.search_api(keyword)
            if not xml_data:
                continue
            
            # 結果をパース
            results = self.parse_xml_results(xml_data, keyword)
            logger.info(f"検索結果: {len(results)} 件")
            total_searched += len(results)
            
            # データベースに保存
            new_items = self.save_to_database(results)
            logger.info(f"新規案件: {len(new_items)} 件")
            
            all_new_items.extend(new_items)
            
            # API負荷対策のため少し待機
            time.sleep(1)
        
        # 検索結果に関わらず通知メールを送信
        logger.info(f"処理完了: 検索総数 {total_searched} 件, 新規案件 {len(all_new_items)} 件")
        self.send_notification(all_new_items)
    
    def test_mail(self):
        """メール送信テスト"""
        logger.info("メール送信テストを開始します")
        
        # テスト用のダミーデータを作成
        test_items = [
            {
                'key': 'TEST_001',
                'project_name': '【テスト】これはテストメールです - サイバーセキュリティシステム構築',
                'organization_name': '【テスト】防衛省',
                'cft_issue_date': datetime.now().strftime('%Y-%m-%d'),
                'category': 'テスト案件',
                'procedure_type': 'テスト入札',
                'location': 'テスト実施場所',
                'tender_submission_deadline': '2025-12-31',
                'opening_tenders_event': '2025-12-31',
                'period_end_time': '2025-12-31',
                'external_document_uri': 'https://example.com/test-document-001',
                'file_type': 'test',
                'file_size': 12345,
                'search_keyword': 'テストキーワード'
            },
            {
                'key': 'TEST_002',
                'project_name': '【テスト】ダミー案件 - ネットワークセキュリティ調査',
                'organization_name': '【テスト】防衛省',
                'cft_issue_date': datetime.now().strftime('%Y-%m-%d'),
                'category': 'テスト役務',
                'procedure_type': 'テスト公募',
                'location': None,  # 欠損データのテスト
                'tender_submission_deadline': None,
                'opening_tenders_event': '2025-12-25',
                'period_end_time': None,
                'external_document_uri': 'https://example.com/test-document-002',
                'file_type': 'test',
                'file_size': None,
                'search_keyword': 'テスト検索'
            }
        ]
        
        # テストメールを送信
        try:
            self.send_test_notification(test_items)
            logger.info("テストメールの送信に成功しました")
        except Exception as e:
            logger.error(f"テストメールの送信に失敗しました: {str(e)}")
            raise
    
    def send_test_notification(self, test_items):
        """テスト用メール通知"""
        smtp_config = self.config['smtp']
        notification_config = self.config['notification']
        
        # メール本文の作成
        now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        body = f"""
【テストメール】官公需情報検索システム

これはメール送信機能のテストメールです。
実際の案件情報ではありません。

テスト実行日時: {now}
機関名: {self.config['organization']}
テスト案件数: {len(test_items)} 件

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ テスト案件詳細（ダミーデータ）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for i, item in enumerate(test_items, 1):
            body += f"\n【テスト案件 {i}】\n"
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
【重要】これはテストメールです。
実際の入札案件ではありませんのでご注意ください。

メール送信設定:
- SMTPサーバー: {smtp_config['server']}:{smtp_config['port']}
- TLS: {'有効' if smtp_config['use_tls'] else '無効'}
- 送信元: {notification_config['from_email']}
- 送信先: {', '.join(notification_config['to_emails'])}

このメールが正常に受信できていれば、
メール送信機能は正しく設定されています。
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
        msg['Subject'] = '【テスト】' + notification_config['subject']
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        try:
            logger.info(f"テストメール送信を開始します")
            
            # タイムアウトを設定（30秒）
            if smtp_config['use_tls']:
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_config['server'], smtp_config['port'], timeout=30)
            
            logger.info("SMTPサーバーに接続しました")
            server.login(smtp_config['username'], smtp_config['password'])
            logger.info("SMTPサーバーにログインしました")
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"テストメールを送信しました")
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP認証エラー: ユーザー名またはパスワードが正しくありません - {str(e)}")
            raise
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP接続エラー: サーバーに接続できません - {str(e)}")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTPエラー: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"メール送信エラー: {type(e).__name__} - {str(e)}")
            raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='官公需情報検索・通知システム')
    parser.add_argument('--no-mail', action='store_true', 
                       help='メール送信をスキップ（テスト用）')
    parser.add_argument('--test-mail', action='store_true',
                       help='テストメールを送信（メール設定の確認用）')
    parser.add_argument('--config', default='config.json',
                       help='設定ファイルのパス（デフォルト: config.json）')
    
    args = parser.parse_args()
    
    # システムを初期化
    notifier = KKJSearchNotifier(args.config)
    
    # テストメール送信モード
    if args.test_mail:
        logger.info("=== テストメール送信モード ===")
        notifier.test_mail()
        logger.info("=== テストメール送信完了 ===")
        sys.exit(0)
    
    # メール送信を無効化（テスト用）
    if args.no_mail:
        logger.info("メール送信は無効化されています（テストモード）")
        def skip_notification(items):
            if items:
                logger.info(f"メール送信をスキップ: 新規案件 {len(items)} 件")
            else:
                logger.info(f"メール送信をスキップ: 新規案件なし")
        notifier.send_notification = skip_notification
    
    # 通常実行
    notifier.run()