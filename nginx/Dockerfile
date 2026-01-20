# This is the correct content for nginx/Dockerfile

# Use a lightweight NGINX base image
FROM nginx:alpine

# Copy your custom NGINX configuration into the container.
# This is the standard location for additional configuration files.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for the NGINX server
EXPOSE 80

# The command to start the NGINX server when the container runs
CMD ["nginx", "-g", "daemon off;"]
