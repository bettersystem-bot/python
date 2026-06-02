FROM python:3.11-slim

WORKDIR /app

# 先装依赖，利用 Docker 层缓存。
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# 默认启动 core service；worker 在 docker-compose 里用不同 command 复用此镜像。
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
