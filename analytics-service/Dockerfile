# Use the Node.js 18 image
FROM node:18

# Set working directory
WORKDIR /app

# Copy source files and install dependencies
COPY package*.json ./

# Resolve conflict by combining or using chosen lines:
RUN apk add --no-cache --virtual .gyp python3 make g++ \
    && npm install --only=production --silent \
    && apk del .gyp

# Uncomment this line if you want to use the simpler npm install command
# RUN npm install --production

# Copy all files into the image
COPY . .

# Expose the port used by this application
EXPOSE 4000

# Set environment variables as needed, then start the app
CMD ["npm", "start"]
