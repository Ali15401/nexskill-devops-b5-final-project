FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
# Ensure devDependencies are installed (so react-scripts is available)
RUN npm ci --silent --include=dev
COPY . .
ARG REACT_APP_LINK_SERVICE_URL
ARG REACT_APP_ANALYTICS_SERVICE_URL
ENV REACT_APP_LINK_SERVICE_URL=$REACT_APP_LINK_SERVICE_URL
ENV REACT_APP_ANALYTICS_SERVICE_URL=$REACT_APP_ANALYTICS_SERVICE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
