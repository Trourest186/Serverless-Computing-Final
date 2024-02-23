FROM node:12-slim
WORKDIR /app
COPY ./package*.json ./
RUN npm install
COPY ./ ./
EXPOSE 3000

# Run the code
CMD [ "npm", "start" ]
