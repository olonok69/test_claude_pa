FROM nginx:alpine

# Install required tools
RUN apk add --no-cache openssl curl

# Remove default config
RUN rm -f /etc/nginx/conf.d/default.conf

# Create directories
RUN mkdir -p /etc/nginx/ssl /var/log/nginx /var/www/certbot

# Copy configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]