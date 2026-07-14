FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_BFF_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_BFF_URL=${NEXT_PUBLIC_BFF_URL}
ENV NODE_ENV=production
ENV PORT=3000

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
