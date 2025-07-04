# Stage 1: Build
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# # Stage 2: Production image to serve static files
# FROM nginx:alpine

# # Remove default nginx static files
# RUN rm -rf /usr/share/nginx/html/*

# # Copy built files from previous stage
# COPY --from=builder /app/dist /usr/share/nginx/html

# # Copy custom nginx config if needed
# # COPY nginx.conf /etc/nginx/nginx.conf

# EXPOSE 80

# CMD ["nginx", "-g", "daemon off;"]

# Stage 2: Run Node server
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 3000
CMD ["node", "./.output/server/index.mjs"]
