# --- Stage 1: install Python deps (cached unless pyproject.toml changes) ---
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false

WORKDIR /app
COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --no-interaction --no-ansi --extras api --without dev --no-root

# Install tabwrap itself so importlib.metadata can resolve the version
# at runtime. Separate layer keeps the heavy dep-install above cacheable.
COPY tabwrap/ tabwrap/
RUN poetry install --no-interaction --no-ansi --only-root

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

# tabwrap is already installed into site-packages (copied above);
# only the runtime config file needs to land in the working dir.
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
