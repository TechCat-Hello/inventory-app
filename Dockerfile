# ベースイメージの指定（Python公式イメージ）
FROM python:3.11-slim

# 作業ディレクトリを /code に設定
WORKDIR /code

# ホストの requirements.txt をコンテナにコピー
COPY requirements.txt /code/

# 必要なPythonパッケージをインストール
RUN pip install --upgrade pip && pip install -r requirements.txt

# ホストのソースコードをすべて /code にコピー
COPY . /code/


