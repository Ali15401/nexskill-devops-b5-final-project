# Start from the official Nginx image
FROM nginx:latest

# Remove the default nginx config file from the image
RUN rm /etc/nginx/nginx.conf

# Copy our new, corrected config file into the image
COPY nginx.conf /etc/nginx/nginx.conf
