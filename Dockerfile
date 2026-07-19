FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY zsm ./zsm
RUN python -m pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim

LABEL org.opencontainers.image.title="Zima Storage Manager" \
      org.opencontainers.image.description="Web UI for safely renaming ZimaOS disk mount records" \
      org.opencontainers.image.source="https://github.com/AngoloInformatico/zima-storage-manager" \
      org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends util-linux \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

ENV ZSM_HOST=0.0.0.0 \
    ZSM_PORT=8765 \
    ZSM_CONFIG=/etc/zsm/config.json \
    ZSM_HOST_NAMESPACE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3)" || exit 1

CMD ["zsm-web"]
