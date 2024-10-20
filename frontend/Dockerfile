FROM node:22

WORKDIR /app

COPY package.json .

RUN npm install

RUN npm install -g vite

# add `/app/node_modules/.bin` to $PATH
ENV PATH /app/node_modules/.bin:$PATH

COPY . .

EXPOSE 3000

CMD vite --host 0.0.0.0 --port 3000