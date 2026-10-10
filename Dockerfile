FROM python:3.11-slim

WORKDIR /app

# 先安装依赖，充分利用镜像层缓存
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 时区：schedule 定时任务按本地时间（Asia/Shanghai）调度
ENV TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

# 拷贝应用代码（backend 内已包含 prompts/、__init__.py）
COPY backend/ ./backend/

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 5000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]
