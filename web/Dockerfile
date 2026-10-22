FROM nginx:alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Add our config
RUN mkdir -p /etc/nginx/snippets
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY security-headers.conf /etc/nginx/snippets/security-headers.conf

# Copy web files
COPY . /usr/share/nginx/html/

# Remove Dockerfile and nginx.conf from served content
RUN rm -f /usr/share/nginx/html/Dockerfile /usr/share/nginx/html/nginx.conf

EXPOSE 80
