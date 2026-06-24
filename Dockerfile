FROM nginx:alpine

# Custom server config: custom 404 page + static-asset caching
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY index.html /usr/share/nginx/html/
COPY privacy.html /usr/share/nginx/html/
COPY terms.html /usr/share/nginx/html/
COPY 404.html /usr/share/nginx/html/
COPY favicon.svg /usr/share/nginx/html/
COPY og-image.png /usr/share/nginx/html/
COPY robots.txt /usr/share/nginx/html/
COPY sitemap.xml /usr/share/nginx/html/
COPY lib/ /usr/share/nginx/html/lib/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
