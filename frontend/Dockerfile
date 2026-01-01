FROM node:18-alpine AS build

WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

COPY package*.json ./

RUN npm install

COPY . .

ARG REACT_APP_LINK_SERVICE_URL
ARG REACT_APP_ANALYTICS_SERVICE_URL
ENV REACT_APP_LINK_SERVICE_URL=${REACT_APP_LINK_SERVICE_URL}
ENV REACT_APP_ANALYTICS_SERVICE_URL=${REACT_APP_ANALYTICS_SERVICE_URL}

RUN npm run build

FROM nginx:stable-alpine AS production

RUN rm -rf /usr/share/nginx/html/*

COPY --from=build /app/build /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
