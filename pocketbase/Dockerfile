# Pinned PocketBase binary for the local-dev compose target (see README.md).
FROM alpine:3.21
ARG PB_VERSION=0.40.6
ARG PB_SHA256=0e1f609158ed945f809f8a02ae012aa0427129c66ebb63c1aee76f2c0309373f
RUN apk add --no-cache ca-certificates unzip \
    && wget -q -O /tmp/pb.zip "https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_linux_amd64.zip" \
    && printf '%s  %s\n' "${PB_SHA256}" /tmp/pb.zip | sha256sum -c - \
    && unzip /tmp/pb.zip -d /usr/local/bin \
    && rm /tmp/pb.zip \
    && addgroup -g 10001 pocketbase \
    && adduser -D -H -u 10001 -G pocketbase pocketbase \
    && mkdir /pb_data \
    && chown 10001:10001 /pb_data
USER 10001:10001
EXPOSE 8090
ENTRYPOINT ["pocketbase"]
