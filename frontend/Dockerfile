FROM node:24-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

EXPOSE 5173
# Dev server on all interfaces; /api is proxied to API_URL (the backend service in docker-compose.yml).
CMD ["npx", "vite", "--host", "0.0.0.0"]
