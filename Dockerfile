FROM python:3.11-slim AS builder

# Keep Python output unbuffered and disable .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Create a virtualenv for reproducible installs.
RUN python -m venv /venv
ENV PATH="/venv/bin:${PATH}"

# Pre-copy metadata to leverage layer caching.
COPY requirements.txt requirements-dev.txt pyproject.toml README.md /app/

# Copy source and tests ahead of editable install.
COPY src /app/src
COPY tests /app/tests
COPY build/pyinstaller /app/build/pyinstaller

# Install dev deps and the package (editable) for testing.
RUN pip install --upgrade pip \
    && pip install -r requirements-dev.txt \
    && pip install -e .

# Run tests during the build to catch issues early.
RUN pytest

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/venv/bin:${PATH}"

WORKDIR /app

# Bring the pre-built virtualenv from the builder.
COPY --from=builder /venv /venv

# Copy only what the runtime needs.
COPY pyproject.toml README.md /app/
COPY src /app/src

# Allow mounting the creative root and SQLite DB for persistence.
VOLUME ["/mnt/c/Projects", "/root/.pipeline_tools"]

# Default to the unified CLI; args are passed through.
ENTRYPOINT ["python", "-m", "pipeline_tools.cli"]
