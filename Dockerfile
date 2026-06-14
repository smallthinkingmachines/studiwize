FROM nginx:alpine

COPY index.html /usr/share/nginx/html/
COPY favicon.svg /usr/share/nginx/html/
COPY og-image.png /usr/share/nginx/html/
COPY robots.txt /usr/share/nginx/html/
COPY lib/ /usr/share/nginx/html/lib/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
