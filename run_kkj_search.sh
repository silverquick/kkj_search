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
