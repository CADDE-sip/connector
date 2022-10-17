FROM alpine:3.16

RUN apk add --no-cache squid && \
  mkdir -p /etc/squid/conf.d && \
  mkdir -p /var/lib/squid && \
  cp /etc/squid/squid.conf /etc/squid/conf.d/default.conf && \
  echo 'include /etc/squid/conf.d/*.conf' > /etc/squid/squid.conf

RUN install -d -o squid -g squid \
                /var/cache/squid \
                /var/log/squid \
                /var/run/squid \
                /var/lib/squid && \
        chmod +x /usr/lib/squid/*

COPY squid-log.conf /etc/squid/conf.d/

EXPOSE 3128
USER squid
CMD ["/usr/sbin/squid", "-NYCd 1"]
