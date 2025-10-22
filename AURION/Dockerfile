# Multi-stage build for AURION
FROM node:18-alpine as frontend-builder
WORKDIR /app
COPY Aurion_frontend/package*.json ./
RUN npm ci --only=production
COPY Aurion_frontend/ .
RUN npm run build

FROM python:3.10-slim as backend
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY AURION-Backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY AURION-Backend/ .

# Copy frontend build
COPY --from=frontend-builder /app/dist ./static

# Create non-root user
RUN useradd -m -u 1000 aurion && chown -R aurion:aurion /app
USER aurion

EXPOSE 8000
CMD ["python", "start_server.py"]