# 使用官方Python镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY environment.yml .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY src/ ./src/
COPY main.py .
COPY scripts/ ./scripts/
COPY prompts/ ./prompts/
COPY evals/ ./evals/
COPY tests/ ./tests/
COPY data/ ./data/

# 创建日志目录
RUN mkdir -p logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 默认命令
CMD ["python", "main.py", "--check-model"]