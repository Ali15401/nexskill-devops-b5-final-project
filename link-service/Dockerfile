# Use Node.js as the base image
FROM node:18-alpine

# Set working directory in the container
WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Create a non-root user and set ownership
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
RUN chown -R nodejs:nodejs /app
USER nodejs

# Expose port 5001
EXPOSE 5001

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
   CMD curl -f http://localhost:5001/health || exit 1

# Start the app
CMD ["node", "server.js"]
