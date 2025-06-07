#!/bin/bash
# setup.sh - 官公需情報検索システム初期セットアップスクリプト

set -e  # エラーが発生したら即座に終了

# 色付き出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 関数定義
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# pyenvの確認とインストール
check_pyenv() {
    if [ ! -d "$HOME/.pyenv" ]; then
        print_info "pyenvをインストールします..."
        
        # 依存パッケージのインストール
        sudo apt update
        sudo apt install -y make build-essential libssl-dev zlib1g-dev \
            libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
            libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev \
            liblzma-dev python3-openssl git
        
        # pyenvのインストール
        git clone https://github.com/pyenv/pyenv.git ~/.pyenv
        
        # pyenv-virtualenvのインストール
        git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
        
        # bashrcに追記
        echo '' >> ~/.bashrc
        echo '# pyenv configuration' >> ~/.bashrc
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
        echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
        echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
        echo 'eval "$(pyenv init -)"' >> ~/.bashrc
        echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
        
        print_success "pyenvをインストールしました"
        print_info "シェルを再起動するか、'source ~/.bashrc'を実行してください"
        exit 0
    else
        print_success "pyenvは既にインストールされています"
    fi
}

# プロジェクトのセットアップ
setup_project() {
    # pyenv環境の読み込み
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)" 2>/dev/null || true
    
    # Python 3.11のインストール
    PYTHON_VERSION="3.11.7"
    print_info "Python $PYTHON_VERSION をインストールしています..."
    if ! pyenv versions | grep -q "$PYTHON_VERSION"; then
        pyenv install $PYTHON_VERSION
        print_success "Python $PYTHON_VERSION をインストールしました"
    else
        print_success "Python $PYTHON_VERSION は既にインストールされています"
    fi
    
    # 仮想環境の作成
    ENV_NAME="kkj-search"
    if ! pyenv versions | grep -q "$ENV_NAME"; then
        print_info "仮想環境 $ENV_NAME を作成しています..."
        pyenv virtualenv $PYTHON_VERSION $ENV_NAME
        print_success "仮想環境を作成しました"
    else
        print_success "仮想環境 $ENV_NAME は既に存在します"
    fi
    
    # プロジェクトディレクトリの作成
    PROJECT_DIR="$HOME/projects/kkj_search"
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # 仮想環境の設定
    pyenv local $ENV_NAME
    print_success "プロジェクトディレクトリを作成し、仮想環境を設定しました"
    
    # スクリプトファイルの確認
    print_info "必要なファイルを確認しています..."
    
    # requirements.txtがない場合は作成
    if [ ! -f "requirements.txt" ]; then
        cat > requirements.txt << 'EOF'
requests==2.31.0
openai>=1.55.2
EOF
        print_success "requirements.txt を作成しました"
    fi
    
    # Pythonパッケージのインストール
    print_info "Pythonパッケージをインストールしています..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "パッケージをインストールしました"
    
    # 実行権限の付与
    if [ -f "kkj_search.py" ]; then
        chmod +x kkj_search.py
        print_success "kkj_search.py に実行権限を付与しました"
    else
        print_error "kkj_search.py が見つかりません。ファイルをコピーしてください"
    fi
    
    if [ -f "kkj_maintenance.py" ]; then
        chmod +x kkj_maintenance.py
        print_success "kkj_maintenance.py に実行権限を付与しました"
    fi
    
    # config.jsonのテンプレート作成
    if [ ! -f "config.json" ] && [ -f "config.json.template" ]; then
        print_info "config.jsonをテンプレートから作成しています..."
        cp config.json.template config.json
        print_success "config.json を作成しました"
        print_info "config.json を編集してSMTP設定とOpenAI APIキーを設定してください"
    elif [ -f "config.json" ]; then
        print_success "config.json は既に存在します"
    else
        print_error "config.json.template が見つかりません"
    fi
    
    # ラッパースクリプトの作成
    create_wrapper_scripts
    
    # ログファイルとデータベースの初期化
    touch kkj_search.log
    touch cron.log
    touch maintenance.log
    print_success "ログファイルを作成しました"
    
    print_info "セットアップが完了しました！"
    print_info "次のステップ:"
    print_info "1. config.json を編集してSMTP設定とOpenAI APIキーを設定してください"
    print_info "2. python kkj_search.py --test-mail でメール設定をテストしてください"
    print_info "3. python kkj_search.py --no-mail で動作確認してください"
    print_info "4. crontab -e でcronの設定を行ってください（crontab.example を参照）"
}

# ラッパースクリプトの作成
create_wrapper_scripts() {
    # 検索用ラッパー
    cat > run_kkj_search.sh << 'EOF'
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
EOF
    chmod +x run_kkj_search.sh
    print_success "run_kkj_search.sh を作成しました"
    
    # メンテナンス用ラッパー
    cat > run_kkj_maintenance.sh << 'EOF'
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
EOF
    chmod +x run_kkj_maintenance.sh
    print_success "run_kkj_maintenance.sh を作成しました"
}

# メイン処理
main() {
    echo "=== 官公需情報検索システム セットアップ ==="
    echo ""
    
    # pyenvの確認
    check_pyenv
    
    # プロジェクトのセットアップ
    setup_project
}

# 実行
main