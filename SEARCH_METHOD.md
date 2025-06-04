# 検索方法の説明

## 現在の検索方法（件名検索）

本システムでは、キーワードは**件名（Project_Name）**に対してのみ検索を行います。

### 検索の仕様

- **検索対象**: 案件の件名のみ
- **マッチング方法**: 前後方・途中一致
- **大文字小文字**: 区別しない（APIの仕様による）

### 検索例

キーワード「サイバー」で検索した場合、以下のような件名がヒットします：

✅ ヒットする例：
- 「**サイバー**セキュリティ対策業務」（前方一致）
- 「情報システムの**サイバー**攻撃対応」（途中一致）
- 「○○に係る**サイバー**関連調査」（途中一致）
- 「ネットワーク及び**サイバー**」（後方一致）

❌ ヒットしない例：
- 件名に「サイバー」が含まれていないが、説明文に含まれている案件

## 全文検索への変更方法

もし、件名だけでなく説明文なども含めて検索したい場合は、以下の修正が必要です：

### kkj_search.pyの修正

```python
def search_api(self, keyword):
    """APIで検索を実行"""
    params = {
        'Organization_Name': self.config['organization'],
        'Query': keyword,  # 全文検索に変更
        # 'Project_Name': keyword,  # 件名検索（現在の設定）
        'Count': 100
    }
```

### 検索方法の違い

| パラメータ | 検索対象 | 用途 |
|----------|---------|------|
| Project_Name | 件名のみ | 特定のキーワードを含む案件を絞り込みたい場合 |
| Query | 全文（件名、説明、場所等） | 幅広く情報を収集したい場合 |

### 注意事項

- **Query（全文検索）**を使用すると、検索結果が大幅に増加する可能性があります
- 検索結果が多すぎる場合は、キーワードをより具体的にすることを推奨します

## 検索パラメータの組み合わせ

より詳細な検索が必要な場合は、複数のパラメータを組み合わせることも可能です：

```python
params = {
    'Organization_Name': self.config['organization'],
    'Project_Name': 'システム',  # 件名に「システム」を含む
    'Category': 1,  # 物品のみ
    'LG_Code': '13',  # 東京都
    'Count': 100
}
```

## キーワード設定のベストプラクティス

### 件名検索に適したキーワード

1. **具体的な業務名**
   - 「保守」「運用」「構築」「調査」

2. **技術用語**
   - 「サイバー」「ネットワーク」「クラウド」

3. **システム名の一部**
   - 「情報システム」「管理システム」

### 避けるべきキーワード

1. **一般的すぎる単語**
   - 「業務」「案件」「令和」

2. **1文字のキーワード**
   - APIがエラーを返す可能性があります

## カスタマイズ例

### 複数の検索方法を併用

```python
# config.jsonに検索方法を追加
{
  "search_method": "project_name",  // "project_name" or "query"
  "keywords": ["サイバー", "セキュリティ"]
}

# kkj_search.pyでの実装
def search_api(self, keyword):
    search_method = self.config.get('search_method', 'project_name')
    params = {
        'Organization_Name': self.config['organization'],
        'Count': 100
    }
    
    if search_method == 'query':
        params['Query'] = keyword
    else:
        params['Project_Name'] = keyword
```

これにより、設定ファイルで検索方法を切り替えることができます。