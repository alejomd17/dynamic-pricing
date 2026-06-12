# ── Etapa 1: Build ────────────────────────────────────────────────────────────
# Imagen grande con todo lo necesario para compilar Next.js
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# La URL del backend se inyecta en build-time
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# ── Etapa 2: Production ────────────────────────────────────────────────────────
# Imagen limpia y liviana (~200 MB vs ~2 GB de la etapa de build)
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Solo copiamos lo que Next.js necesita para correr
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
