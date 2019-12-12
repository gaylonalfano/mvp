FROM node:lts-alpine as build
WORKDIR /chica
ENV PATH /chica/node_modules/.bin:$PATH

COPY package.json /chica/package.json
RUN npm install --silent && npm install @vue/cli
COPY . /chica
RUN npm run build

# production environment
FROM nginx:mainline-alpine
COPY --from=build /chica/dist /usr/share/nginx/html
RUN rm /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
