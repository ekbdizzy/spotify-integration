FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set work directory
WORKDIR /app

# Copy uv configuration files
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy project files
COPY project/ ./project/

# Set environment variables
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV PATH="/root/.local/bin:$PATH"

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "python", "project/manage.py", "runserver", "0.0.0.0:8000"]
