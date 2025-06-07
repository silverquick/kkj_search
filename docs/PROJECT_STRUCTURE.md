# 官公需情報検索・通知システム プロジェクト構造

## ディレクトリ構造

```
~/projects/kkj_search/
├── kkj_search.py           # メイン検索・通知スクリプト
├── kkj_maintenance.py      # データベースメンテナンススクリプト
├── config.json            # 設定ファイル（config.json.templateから作成）
├── config.json.template   # 設定ファイルのテンプレート
├── requirements.txt       # Python依存パッケージリスト
├── run_kkj_search.sh      # cron実行用ラッパースクリプト
├── run_kkj_maintenance.sh # メンテナンス用ラッパースクリプト
├── crontab.example        # crontab設定の例
├── kkj_search.db          # SQLiteデータベース（自動生成）
├── kkj_search.log         # アプリケーションログ
├── cron.log               # cron実行ログ
├── maintenance.log        # メンテナンスログ
├── README.md              # セットアップガイド
├── LICENSE                # ライセンスファイル
├── .gitignore            # Git除外設定
├── .python-version        # pyenv環境指定ファイル（自動生成）
├── docs/                  # ドキュメントフォルダ
│   ├── README_ORIGINAL.md     # オリジナルのREADME
│   ├── PROJECT_STRUCTURE.md   # このファイル
│   ├── TROUBLESHOOTING.md     # トラブルシューティングガイド
│   ├── SMTP_TROUBLESHOOT.md   # SMTP設定のトラブルシューティング
│   ├── SEARCH_METHOD.md       # 検索方法の説明
│   └── USAGE_EXAMPLES.md      # 使用例とユースケース
└── samples/               # サンプルファイルフォルダ
    ├── EMAIL_SAMPLE.txt       # 通常メールのサンプル
    ├── NO_ITEMS_EMAIL_SAMPLE.txt  # 新規案件なしメールのサンプル
    └── TEST_EMAIL_SAMPLE.txt  # テストメールのサンプル
```

## ファイル説明

### 実行ファイル

1. **kkj_search.py**
   - 官公需情報ポータルサイトAPIを使用して検索
   - 新規案件をデータベースに保存
   - メール通知機能
   - OpenAI APIによるURL要約機能（オプション）

2. **kkj_maintenance.py**
   - 古いデータの削除
   - データベースの最適化（VACUUM）
   - 統計情報の表示

3. **run_kkj_search.sh**
   - cronから実行するためのラッパー
   - pyenv環境を適切に読み込む

4. **run_kkj_maintenance.sh**
   - メンテナンス処理用のラッパー
   - 定期的なクリーンアップに使用

### 設定ファイル

5. **config.json**
   - 検索条件（機関名、キーワード）
   - SMTPサーバー設定
   - 通知先メールアドレス
   - データベースパス
   - OpenAI API設定（オプション）

6. **config.json.template**
   - config.jsonのテンプレート
   - 初回セットアップ時にコピーして使用

7. **requirements.txt**
   - Python依存パッケージの管理
   - `pip install -r requirements.txt`で一括インストール

8. **crontab.example**
   - crontab設定の例
   - 定期実行の設定方法を記載

### 設定ファイル（続き）

9. **crontab.example**
   - crontab設定の例
   - 定期実行の設定方法を記載

### データファイル

10. **kkj_search.db**
    - SQLiteデータベース
    - 検索結果を永続化

### ログファイル

11. **kkj_search.log**
    - メインスクリプトの実行ログ
    - エラー追跡に使用

12. **cron.log**
    - cron経由での実行ログ

13. **maintenance.log**
    - メンテナンス処理のログ

### ドキュメント

15. **README.md**
    - インストール手順
    - 使用方法
    - 基本的なトラブルシューティング

16. **docs/README_ORIGINAL.md**
    - オリジナルのREADME（参考資料）

17. **docs/PROJECT_STRUCTURE.md**
    - プロジェクト構造の説明（このファイル）

18. **docs/TROUBLESHOOTING.md**
    - 詳細なトラブルシューティングガイド

19. **docs/SMTP_TROUBLESHOOT.md**
    - SMTP設定に特化したトラブルシューティング

20. **docs/SEARCH_METHOD.md**
    - 検索方法と仕様の詳細説明

21. **docs/USAGE_EXAMPLES.md**
    - 実践的な使用例とユースケース

### サンプルファイル

22. **samples/EMAIL_SAMPLE.txt**
    - 新規案件がある場合の通知メールサンプル

23. **samples/NO_ITEMS_EMAIL_SAMPLE.txt**
    - 新規案件がない場合の通知メールサンプル

24. **samples/TEST_EMAIL_SAMPLE.txt**
    - テストメール送信時のサンプル

### その他

14. **LICENSE**
    - プロジェクトのライセンス情報

15. **.gitignore**
    - Gitで管理しないファイルの設定

### 自動生成ファイル

16. **.python-version**
    - pyenvが使用するPython環境指定
    - `pyenv local`コマンドで自動生成

## データフロー

```
1. config.json（設定）
   ↓
2. kkj_search.py（検索実行）
   ↓
3. 官公需API（データ取得）
   ↓
4. kkj_search.db（保存）
   ↓
5. メール通知（新規案件のみ）
```

## 定期実行フロー

```
crontab
  ↓
run_kkj_search.sh（pyenv環境設定）
  ↓
kkj_search.py（検索・通知）
  ↓
ログ出力（cron.log, kkj_search.log）
```

## メンテナンスフロー

```
crontab（週次など）
  ↓
run_kkj_maintenance.sh（pyenv環境設定）
  ↓
kkj_maintenance.py（クリーンアップ）
  ↓
ログ出力（maintenance.log）
```

## セキュリティ考慮事項

- **config.json**: SMTPパスワードが含まれるため、適切な権限設定が必要
  ```bash
  chmod 600 config.json
  ```

- **kkj_search.db**: 検索結果データが含まれる
  ```bash
  chmod 644 kkj_search.db
  ```

- **ログファイル**: エラー情報が含まれる可能性
  ```bash
  chmod 644 *.log
  ```

## バックアップ推奨ファイル

- config.json（設定情報）
- kkj_search.db（データベース）
- カスタマイズしたスクリプト類

## 開発時の注意点

1. **Python環境**
   - 必ずプロジェクトディレクトリで作業
   - pyenv環境が有効になっていることを確認

2. **依存関係**
   - 新しいパッケージを追加したらrequirements.txtを更新
   - `pip freeze > requirements.txt`

3. **テスト実行**
   - 本番環境のconfig.jsonをコピーしてテスト環境を作成
   - テスト用のSMTP設定を使用

4. **ログ管理**
   - 定期的にログファイルのサイズを確認
   - 必要に応じてログローテーションを設定