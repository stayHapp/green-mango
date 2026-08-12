FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ARG PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /app

# 适配Debian trixie 新sources格式，替换阿里云源
RUN echo "Types: deb" > /etc/apt/sources.list.d/debian.sources \
    && echo "URIs: https://mirrors.aliyun.com/debian" >> /etc/apt/sources.list.d/debian.sources \
    && echo "Suites: trixie trixie-updates trixie-backports" >> /etc/apt/sources.list.d/debian.sources \
    && echo "Components: main contrib non-free non-free-firmware" >> /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./

RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-deps --no-build-isolation .

EXPOSE 8010
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010", "--workers", "2"]
