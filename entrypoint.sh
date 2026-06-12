#!/bin/bash

echo "Iniciando Backend (FastAPI)..."
cd /app/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*' &

echo "Iniciando Frontend (Next.js)"
cd /app/frontend
HOSTNAME="0.0.0.0" PORT=3000 node server.js &

echo "Iniciando Nginx"
nginx -g "daemon off;"
