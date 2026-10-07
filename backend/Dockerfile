FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend source + web frontend (served by FastAPI)
COPY backend/ /app/backend/
COPY web/ /app/web/

# Create data directory for SQLite (will be mounted as volume)
RUN mkdir -p /app/data

# Expose API port
EXPOSE 5000

# Seed the database then run the server
CMD ["sh", "-c", "python -m backend.api.seed && uvicorn backend.api.main:app --host 0.0.0.0 --port 5000"]
