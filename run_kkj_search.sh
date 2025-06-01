#!/bin/bash
# run_kkj_search.sh - 検索スクリプト実行用ラッパー

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

# 終了コードを保存
EXIT_CODE=$?

# エラーが発生した場合はログに記録
if [ $EXIT_CODE -ne 0 ]; then
    echo "[$(date)] Error occurred with exit code: $EXIT_CODE" >> cron.log
fi

# 終了コードを返す
exit $EXIT_CODE

---

#!/bin/bash
# run_kkj_maintenance.sh - メンテナンススクリプト実行用ラッパー

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

# 終了コードを返す
exit $?