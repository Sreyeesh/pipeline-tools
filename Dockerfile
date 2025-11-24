FROM python:3.11-slim

# Keep Python output unbuffered and disable .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Pre-copy metadata to leverage Docker layer caching.
COPY pyproject.toml README.md /app/
COPY src /app/src

# Create expected folders and install the package.
RUN mkdir -p /mnt/c/Projects /root/.pipeline_tools \
    && pip install --upgrade pip \
    && pip install .

# Allow mounting the creative root and SQLite DB for persistence.
VOLUME ["/mnt/c/Projects", "/root/.pipeline_tools"]

# Default to the project creator tool; override CMD to call other modules.
ENTRYPOINT ["python", "-m"]
CMD ["pipeline_tools.tools.project_creator.main"]
