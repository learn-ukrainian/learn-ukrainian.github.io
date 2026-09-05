# Pinned PocketBase binary for the local-dev compose target (see README.md).
FROM alpine:3.21
ARG PB_VERSION=0.40.2
RUN apk add --no-cache ca-certificates unzip \
    && wget -q -O /tmp/pb.zip "https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_linux_amd64.zip" \
    && unzip /tmp/pb.zip -d /usr/local/bin \
    && rm /tmp/pb.zip
EXPOSE 8090
ENTRYPOINT ["pocketbase"]
