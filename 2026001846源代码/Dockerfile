FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# 阿里云实例走阿里云镜像，比官方源快一个数量级
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY server/backend/requirements.txt /app/requirements.txt
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=120 -r /app/requirements.txt

COPY server /app/server

WORKDIR /app/server/backend

EXPOSE 5000

CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "--timeout", "180", "unified_app:create_unified_app()"]
