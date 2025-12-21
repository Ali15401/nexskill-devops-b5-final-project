FROM node:18 AS build
WORKDIR /app
COPY . .

RUN npm install
RUN echo "REACT_APP_LINK_SERVICE_URL=http://localhost:3000" > .env
RUN echo "REACT_APP_ANALYTICS_SERVICE_URL=http://localhost:4000" >> .env
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
