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

# RUN apt-get update && apt-get install -y \
#     libpango-1.0-0 \
#     libpangocairo-1.0-0 \
#     libcairo2 \
#     libgdk-pixbuf2.0-0 \
#     libffi-dev \
#     libgobject-2.0-0 \
#     libglib2.0-0 \
#     fonts-liberation \
#     fonts-dejavu-core \
#     && apt-get clean
