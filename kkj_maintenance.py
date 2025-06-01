#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
import os
from datetime import datetime, timedelta
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KKJDatabaseMaintenance:
    def __init__(self, config_file='config.json'):
        """初期化"""
        self.config = self.load_config(config_file)
        self.db_path = self.config['database']['path']
        
    def load_config(self, config_file):
        """設定ファイルの読み込み"""
        if not os.path.exists(config_file):
            logger.error(f"設定ファイル {config_file} が見つかりません")
            return None
            
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def delete_old_records(self, days=90):
        """指定日数より古いレコードを削除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 削除対象の日付を計算
        delete_date = datetime.now() - timedelta(days=days)
        
        try:
            # 削除前の件数を取得
            cursor.execute("SELECT COUNT(*) FROM search_results WHERE created_at < ?", 
                          (delete_date.strftime('%Y-%m-%d %H:%M:%S'),))
            delete_count = cursor.fetchone()[0]
            
            if delete_count > 0:
                # 削除実行
                cursor.execute("DELETE FROM search_results WHERE created_at < ?", 
                              (delete_date.strftime('%Y-%m-%d %H:%M:%S'),))
                conn.commit()
                logger.info(f"{days}日以前の {delete_count} 件のレコードを削除しました")
            else:
                logger.info(f"{days}日以前のレコードはありません")
                
        except sqlite3.Error as e:
            logger.error(f"データベースエラー: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    def vacuum_database(self):
        """データベースの最適化"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("VACUUM")
            logger.info("データベースを最適化しました")
        except sqlite3.Error as e:
            logger.error(f"最適化エラー: {str(e)}")
        finally:
            conn.close()
    
    def show_statistics(self):
        """データベースの統計情報を表示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 全レコード数
            cursor.execute("SELECT COUNT(*) FROM search_results")
            total_count = cursor.fetchone()[0]
            
            # キーワード別件数
            cursor.execute("""
                SELECT search_keyword, COUNT(*) as count 
                FROM search_results 
                GROUP BY search_keyword 
                ORDER BY count DESC
            """)
            keyword_stats = cursor.fetchall()
            
            # カテゴリ別件数
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM search_results 
                GROUP BY category 
                ORDER BY count DESC
            """)
            category_stats = cursor.fetchall()
            
            # 最古と最新のレコード日時
            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM search_results")
            date_range = cursor.fetchone()
            
            print("\n=== データベース統計情報 ===")
            print(f"総レコード数: {total_count}")
            print(f"\nデータ期間: {date_range[0]} 〜 {date_range[1]}")
            
            print("\n--- キーワード別件数 ---")
            for keyword, count in keyword_stats:
                print(f"{keyword}: {count}件")
                
            print("\n--- カテゴリ別件数 ---")
            for category, count in category_stats:
                if category:
                    print(f"{category}: {count}件")
                    
            # データベースファイルサイズ
            if os.path.exists(self.db_path):
                size = os.path.getsize(self.db_path)
                print(f"\nデータベースファイルサイズ: {size / 1024 / 1024:.2f} MB")
                
        except sqlite3.Error as e:
            logger.error(f"統計情報取得エラー: {str(e)}")
        finally:
            conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='官公需情報データベースメンテナンス')
    parser.add_argument('--delete-days', type=int, default=90,
                       help='指定日数より古いレコードを削除 (デフォルト: 90日)')
    parser.add_argument('--vacuum', action='store_true',
                       help='データベースの最適化を実行')
    parser.add_argument('--stats', action='store_true',
                       help='統計情報を表示')
    
    args = parser.parse_args()
    
    maintenance = KKJDatabaseMaintenance()
    
    if args.stats:
        maintenance.show_statistics()
    else:
        maintenance.delete_old_records(args.delete_days)
        if args.vacuum:
            maintenance.vacuum_database()