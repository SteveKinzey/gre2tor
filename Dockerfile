FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_DEBUG=0 \
    DATABASE_PATH=/data/gre2tor.sqlite3 \
    INSTANCE_PATH=/data \
    GRE2TOR_DISABLE_UPDATE_CHECK=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

COPY . .

RUN mkdir -p /data && chown -R appuser:appuser /data /app
USER appuser

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "120", "app:app"]
