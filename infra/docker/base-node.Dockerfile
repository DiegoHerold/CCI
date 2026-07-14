FROM node:22-alpine

ENV NODE_ENV=production
WORKDIR /app
RUN addgroup -S cci && adduser -S cci -G cci
