# --- STAGE 1: Build the React Application ---
# This stage uses the full Node.js image to install dependencies and build the static files.
FROM node:18-alpine AS build

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the production-ready static files. This creates a 'build' folder.
RUN npm run build

# --- STAGE 2: Serve the Static Files ---
# This stage uses a tiny, lightweight web server image to serve the files we just built.
FROM node:18-alpine

# We need the 'serve' package to host our static files.
RUN npm install -g serve

# Set the working directory
WORKDIR /app

# Copy the 'build' folder from the previous stage into the current stage.
COPY --from=build /app/build .

# Expose port 3000
EXPOSE 3000

# The command to start the server. It will serve the contents of the current folder.
# The '-s' flag is important; it tells 'serve' to handle single-page applications correctly.
# Ensure your start command binds to 0.0.0.0
CMD ["npm", "start", "--", "--host", "0.0.0.0", "--port", "3000"]
