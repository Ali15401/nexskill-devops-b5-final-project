# analytics-service: Node.js app Dockerfile (production + optional test target)
#
# - Build/install dependencies in image
# - Small runtime image (single-stage) using node:18-alpine
# - Optional `test` target to run tests inside a container image
#
# Notes:
# - Make sure analytics-service/package.json exists and contains a "test" script.
# - If native modules must be compiled (rare), the temporary .gyp packages are installed for the install step and removed afterwards.

####################
# Default runtime image
####################
FROM node:18-alpine AS runtime

WORKDIR /app

# Set production env & port (adjust if your app uses a different port)
ENV NODE_ENV=production
ENV PORT=4000

# Copy package manifest(s) first to leverage Docker cache
COPY package*.json ./

# Install only production dependencies.
# If you need devDependencies in the image (e.g. for build), change accordingly.
# Some packages require build tools; we install them temporarily as a virtual package (.gyp) and remove afterwards.
RUN apk add --no-cache --virtual .gyp python3 make g++ \
    && (npm ci --only=production --silent || npm install --only=production --silent) \
    && apk del .gyp

# Copy application source
COPY . .

# Expose the port the app listens on
EXPOSE 4000

# Default command to start the service (ensure package.json has a "start" script)
CMD ["npm", "start"]

####################
# Optional: test target
# You can run: docker build --target test -t analytics-test ./analytics-service
# Or simply use docker-compose run --rm analytics-service sh -lc "npm install && npm test"
####################
FROM node:18-alpine AS test

WORKDIR /app
COPY package*.json ./

# Install all devDependencies for running tests (use legacy-peer-deps to avoid peer dep issues)
RUN npm install --legacy-peer-deps --silent

COPY . .

# Run tests as the container's default command (CI may override this)
CMD ["sh", "-c", "npm test -- --watchAll=false"]
