FROM python:3.14-alpine AS runtime

LABEL org.opencontainers.image.source="https://github.com/Digital-Deadlock/stream-keeper" \
      org.opencontainers.image.description="Experimental go2rtc MSE consumer sidecar for Frigate" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt

COPY src ./src

USER 65532:65532

ENTRYPOINT ["python", "-m", "src.main"]

