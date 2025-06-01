#!/bin/bash
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
