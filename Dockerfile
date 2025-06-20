# ベースイメージの指定（Python公式イメージ）
FROM python:3.11-slim

# 必要なシステムパッケージと日本語フォントをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    fonts-noto-cjk \
    && apt-get clean

# 作業ディレクトリを /code に設定
WORKDIR /code

# ホストの requirements.txt をコンテナにコピー
COPY requirements.txt /code/

# Pythonパッケージのインストール
RUN pip install --upgrade pip && pip install -r requirements.txt

# ホストのソースコードをすべて /code にコピー
COPY . /code/


