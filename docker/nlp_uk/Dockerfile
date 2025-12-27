# nlp_uk Docker container with HTTP API for VESUM word validation
# Optimized from https://github.com/brown-uk/nlp_uk/blob/master/Dockerfile
#
# Usage:
#   docker build -t nlp-uk-api ./docker/nlp_uk
#   docker run -d -p 8899:8899 --name nlp-uk nlp-uk-api
#
# API:
#   POST /validate  {"words": ["слово", "привіт"]}
#   GET  /health    {"status": "ok"}
#   POST /tag       {"text": "Привіт, світе!"}

FROM ubuntu:24.04 AS builder

# Install dependencies in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless \
    unzip \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Download and extract Gradle
ARG GRADLE_VERSION=8.14.3
RUN curl -sL "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" \
    -o /tmp/gradle.zip \
    && unzip -q /tmp/gradle.zip -d /opt/gradle \
    && ln -s /opt/gradle/gradle-${GRADLE_VERSION} /opt/gradle/latest \
    && rm /tmp/gradle.zip

# Clone nlp_uk repository
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && git clone --depth 1 https://github.com/brown-uk/nlp_uk.git /opt/nlp_uk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/nlp_uk

# Clear stats and pre-build (downloads VESUM dictionary)
RUN rm -f /opt/nlp_uk/src/main/resources/ua/net/nlp/tools/stats/* \
    && /opt/gradle/latest/bin/gradle --no-daemon compileGroovy copyRuntimeLibs

# Test the build works
RUN echo "Привіт" > /tmp/test.txt \
    && /opt/gradle/latest/bin/gradle --no-daemon --offline tagText -PlocalLib -Pargs="-i /tmp/test.txt" \
    && rm /tmp/test.txt

# ============================================
# Runtime stage
# ============================================
FROM ubuntu:24.04

# nlp_uk needs full JDK (Groovy compilation at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Gradle and nlp_uk from builder
COPY --from=builder /opt/gradle /opt/gradle
COPY --from=builder /opt/nlp_uk /opt/nlp_uk

# Setup Python virtual environment and install Flask
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir flask

WORKDIR /opt/nlp_uk

# Copy HTTP API server
COPY server.py /opt/nlp_uk/server.py

# Expose API port
EXPOSE 8899

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8899/health || exit 1

# Run the Flask server
ENV PATH="/opt/gradle/latest/bin:/opt/venv/bin:${PATH}"
CMD ["python3", "/opt/nlp_uk/server.py"]
