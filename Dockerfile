# --- Stage 1: install Python deps (cached unless pyproject.toml/uv.lock changes) ---
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./

# Install runtime dependencies into the system environment (stage 2 copies
# site-packages, so deps must live there — not in a .venv). --no-emit-project
# excludes tabwrap itself, keeping this heavy layer cacheable across source changes.
RUN uv export --frozen --no-dev --extra api --no-emit-project --no-hashes -o requirements.txt \
    && uv pip install --system --no-cache -r requirements.txt

# Install tabwrap itself as an editable install so importlib.metadata can resolve
# the version at runtime; the .pth in site-packages points back to /app.
COPY tabwrap/ tabwrap/
RUN uv pip install --system --no-cache --no-deps -e .

# --- Stage 2: runtime image with TeX + system deps ---
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        texlive-full \
        imagemagick \
        pdf2svg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ImageMagick policy: allow PDF conversion (handles both IM6 and IM7 paths)
RUN for f in /etc/ImageMagick-6/policy.xml /etc/ImageMagick-7/policy.xml; do \
        [ -f "$f" ] && sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' "$f"; \
    done; true

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Application code. Required because ``uv sync`` in stage 1 produces an editable
# install — the .pth in site-packages points back here, so the source must exist
# at this path at runtime.
COPY tabwrap/ tabwrap/
COPY gunicorn.conf.py .

# Non-root user
RUN useradd -m -s /bin/bash appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "tabwrap.api:app"]
