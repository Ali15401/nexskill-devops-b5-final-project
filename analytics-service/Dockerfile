FROM node:18-alpine AS test

WORKDIR /app

COPY package*.json ./

RUN npm run build

COPY . .

CMD ["sh", "-c", "npm test -- --watchAll=false"]
