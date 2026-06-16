# ── Etapa 1: Build Backend ───────────────────────────────────────────────────
FROM python:3.11-slim AS backend-builder

WORKDIR /app/backend

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv export --no-dev --no-hashes -o /requirements.txt

COPY backend/ .

# ── Etapa 2: Build Frontend ──────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ .

ARG NEXT_PUBLIC_API_URL=/dynamic_pricing/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# ── Etapa 3: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

COPY --from=backend-builder /requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /app/backend

# Generar sesión inicial con los modelos entrenados (se guarda en la imagen)
RUN cd /app/backend && python scripts/create_session.py

COPY --from=frontend-builder /app/frontend/public /app/frontend/public
COPY --from=frontend-builder /app/frontend/.next/standalone /app/frontend
COPY --from=frontend-builder /app/frontend/.next/static /app/frontend/.next/static

COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 80

CMD ["/app/entrypoint.sh"]
