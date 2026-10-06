FROM python:3.13-slim

# Tránh tạo .pyc files và đảm bảo log hiện realtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cài uv (fast package manager)
RUN pip install --no-cache-dir uv

# Copy dependency files trước (cache layer)
COPY pyproject.toml ./

# Cài dependencies (không cài dev deps)
RUN uv sync --no-dev --frozen || uv pip install -e .

# Copy source code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/')" || exit 1

# Khởi động server
CMD ["python", "-m", "uvicorn", "room_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
