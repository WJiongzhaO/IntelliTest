# Override via docker-compose build.args when Docker Hub is unreachable
ARG NODE_IMAGE=node:20-alpine
FROM ${NODE_IMAGE}

WORKDIR /app

COPY package*.json ./
RUN npm config set registry https://registry.npmmirror.com \
    && npm ci

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
