# Multi-stage build: build React app, then serve with nginx
FROM node:18 AS build
WORKDIR /app

# Copy package files first to leverage Docker cache
COPY package*.json ./

# Install all dependencies (including devDependencies needed by react-scripts).
# Use --legacy-peer-deps for more tolerant resolution inside the container.
RUN npm install --legacy-peer-deps --silent

# Copy source and build (REACT_APP_* are baked in at build time)
COPY . .
ARG REACT_APP_LINK_SERVICE_URL=http://localhost:3000
ARG REACT_APP_ANALYTICS_SERVICE_URL=http://localhost:4000
ENV REACT_APP_LINK_SERVICE_URL=$REACT_APP_LINK_SERVICE_URL
ENV REACT_APP_ANALYTICS_SERVICE_URL=$REACT_APP_ANALYTICS_SERVICE_URL

RUN npm run build

# Production image
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
