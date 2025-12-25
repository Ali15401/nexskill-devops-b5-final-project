# Replace "FROM <minimal-image>" with the Node.js image
FROM node:18

# Set working directory
WORKDIR /app

# Copy source files and install dependencies
COPY package*.json ./
<<<<<<< HEAD

RUN apk add --no-cache --virtual .gyp python3 make g++ \
    && npm install --only=production --silent \
    && apk del .gyp
=======
RUN npm install --production
>>>>>>> df379995f14e4363d546b330090f2e300265c88b

COPY . .

EXPOSE 4000

# Set environment variables as needed, then start the app
CMD ["npm", "start"]

