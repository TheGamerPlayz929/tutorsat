FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY satprep/ ./satprep/
COPY web/ ./web/
COPY run.py ./

RUN useradd --system --uid 10001 satprep \
    && mkdir -p /data \
    && chown -R satprep:satprep /data

USER satprep

VOLUME ["/data"]

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/health', timeout=4)"

CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8765", \
     "--db", "/data/satprep.db"]
