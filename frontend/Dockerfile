# ── Stage 1: Build React app ──────────────────────────────────────
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files first — cached if unchanged
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copy source and build
COPY . .

# Set the API URL for production build
# This gets baked into the static files at build time
ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build


# ── Stage 2: Serve with Nginx ─────────────────────────────────────
# Nginx is a fast, lightweight web server
# Serving React's static build files through Nginx is the
# correct production approach — not `npm start`
FROM nginx:alpine

# Copy built React files to Nginx's web root
COPY --from=builder /app/build /usr/share/nginx/html

# Custom Nginx config — handles React Router
# Without this, refreshing on /analyze/RELIANCE.NS returns 404
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]