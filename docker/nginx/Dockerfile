FROM nginx:1.31-alpine

RUN rm -f /etc/nginx/conf.d/default.conf
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf

USER nginx
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
