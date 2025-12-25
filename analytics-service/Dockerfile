FROM node:18-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=4000

COPY package*.json ./

RUN apk add --no-cache --virtual .gyp python3 make g++ \
    && npm install --only=production \
    && apk del .gyp

COPY . .

EXPOSE 4000

CMD ["npm", "start"]
