FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml hatch.toml README.md LICENSE datasette.yml ./
COPY openworld_specialty_chemicals ./openworld_specialty_chemicals
COPY scripts ./scripts

RUN pip install --no-cache-dir uv
RUN uv pip install -e ".[all]"

EXPOSE 8000
CMD ["openworld-chem", "dashboard", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /src
RUN pip install --upgrade pip uv
COPY pyproject.toml hatch.toml README.md LICENSE ./
COPY openworld_specialty_chemicals ./openworld_specialty_chemicals
RUN uv pip install .[all] --target /opt/app

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY --from=builder /opt/app /opt/app
ENV PYTHONPATH=/opt/app

# Create non-root user
RUN useradd -m -u 10001 appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import sys, urllib.request; \
    try: \
        with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3) as r: \
            sys.exit(0 if r.status==200 else 1) \
    except Exception: \
        sys.exit(1)"

CMD ["openworld-chem", "dashboard", "--host", "0.0.0.0", "--port", "8000"]

