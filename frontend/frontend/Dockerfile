# Multi-stage build: build React app, then serve with nginx
FROM node:18 AS build
WORKDIR /app

# Install dependencies (including devDependencies required by react-scripts)
COPY package*.json ./
RUN npm ci --silent --production=false

# Copy source, accept build-time variables and build
COPY . .
ARG REACT_APP_LINK_SERVICE_URL=http://localhost:3000
ARG REACT_APP_ANALYTICS_SERVICE_URL=http://localhost:4000
ENV REACT_APP_LINK_SERVICE_URL=$REACT_APP_LINK_SERVICE_URL
ENV REACT_APP_ANALYTICS_SERVICE_URL=$REACT_APP_ANALYTICS_SERVICE_URL

# Build the app (react-scripts reads REACT_APP_* at build time)
RUN npm run build

# Production image
FROM nginx:alpine
# Copy build output to nginx html folder
COPY --from=build /app/build /usr/share/nginx/html
# Use a simple config that falls back to index.html for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
