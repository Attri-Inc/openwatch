FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml requirements.txt ./
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY scripts/ ./scripts/
COPY run_mcp.py ./

RUN mkdir -p /data
ENV OPENWATCH_DB=/data/openwatch.db \
    OPENWATCH_HOST=0.0.0.0 \
    OPENWATCH_PORT=8788

EXPOSE 8788

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8788"]
