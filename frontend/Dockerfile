FROM node:18 AS builder
WORKDIR /src

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM node:18 AS runner
WORKDIR /app

COPY --from=builder /src/public ./public
COPY --from=builder /src/.next ./.next
COPY --from=builder /src/node_modules ./node_modules
COPY --from=builder /src/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
