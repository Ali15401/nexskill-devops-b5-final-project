# --- STAGE 1: Build the React Application ---
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# --- STAGE 2: Serve the Static Files ---
FROM node:18-alpine

# We need the 'serve' package to host our static files.
RUN npm install -g serve

WORKDIR /app

# Copy the 'build' folder from the previous stage.
COPY --from=build /app/build .

EXPOSE 3000

# --- THIS IS THE FIX ---
# Start the server and tell it to listen on all interfaces (0.0.0.0).
CMD ["serve", "-s", ".", "-l", "3000"]
