FROM nginx:1.27-alpine

RUN apk add --no-cache openssl

COPY entrypoint.sh /usr/local/bin/lab-nginx-entrypoint
RUN chmod +x /usr/local/bin/lab-nginx-entrypoint

CMD ["/usr/local/bin/lab-nginx-entrypoint"]
