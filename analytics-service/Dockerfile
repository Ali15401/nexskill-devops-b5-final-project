# analytics-service: Node.js app
FROM node:18-alpine

WORKDIR /app

# Copy package definitions and install dependencies
COPY package*.json ./
# Use npm ci for reproducible install; if you need devDependencies during runtime, remove --only=production
RUN npm ci --only=production

# Copy the rest of the source
COPY . .

# Expose port used by analytics service (adjust if different)
EXPOSE 4000

# Default command: start the service; ensure package.json has an appropriate "start" script
CMD ["npm", "start"]
