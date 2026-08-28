FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=10 --start-period=20s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && python -m scripts.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
