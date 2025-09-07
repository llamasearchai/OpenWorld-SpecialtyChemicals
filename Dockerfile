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
# Prepare writable directories
RUN mkdir -p /app/data /app/artifacts /app/reports /app/logs /app/provenance /app/lineage \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import sys, urllib.request; \
    try: \
        with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3) as r: \
            sys.exit(0 if r.status==200 else 1) \
    except Exception: \
        sys.exit(1)"
VOLUME ["/app/data","/app/artifacts","/app/reports","/app/logs","/app/provenance","/app/lineage"]

# Use module invocation to avoid reliance on console scripts in PATH
CMD ["python","-m","openworld_specialty_chemicals.cli","dashboard","--host","0.0.0.0","--port","8000"]
