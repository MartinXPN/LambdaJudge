# syntax=docker/dockerfile:1
FROM public.ecr.aws/lambda/python:3.14 AS base
WORKDIR ${LAMBDA_TASK_ROOT}

# Initial setup
RUN python -m pip install --upgrade cryptography dataclasses-json psutil

# Run the lambda function handler
CMD [ "coderunners.app.run_code_lambda" ]


FROM base AS c
RUN dnf install -y gcc && dnf clean all && rm -rf /var/cache/dnf
COPY --parents models.py coderunners/*.py ./


FROM base AS cpp
RUN dnf install -y gcc-c++ clang-tools-extra libasan && dnf clean all && rm -rf /var/cache/dnf
COPY --parents models.py coderunners/*.py ./


FROM base AS csharp
RUN dnf install -y tar gzip findutils libicu && dnf clean all && rm -rf /var/cache/dnf
ADD https://dot.net/v1/dotnet-install.sh ./dotnet-install.sh
RUN sh dotnet-install.sh --version latest
RUN mv /root/.dotnet /var/dotnet && rm -f ./dotnet-install.sh

# 1. Enable detection of running in a container
# 2. Lambda is opinionated about installing tooling under /var
# 3. Don't display welcome message on first run
# 4. Disable Microsoft's telemetry collection
# 5. Skip workload integrity checks (they require internet access and fail after several seconds)
# 6. Disable workload update notifications
# 7. Set HOME to a writable directory
ENV \
    DOTNET_RUNNING_IN_CONTAINER=true \
    DOTNET_CLI_HOME=/tmp \
    DOTNET_NOLOGO=true \
    DOTNET_CLI_TELEMETRY_OPTOUT=true \
    DOTNET_SKIP_WORKLOAD_INTEGRITY_CHECK=true \
    DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE=true \
    HOME=/tmp

# Cache the project template and dependencies to speed up cold starts
RUN /var/dotnet/dotnet new console --force --name program --output /var/task/coderunners/csharp_template && \
    rm /var/task/coderunners/csharp_template/Program.cs && \
    mkdir -p /var/task/coderunners/csharp_template/Submission && \
    printf '%s\n' 'internal static class Program { private static void Main() { } }' \
      > /var/task/coderunners/csharp_template/Submission/main.cs && \
    /var/dotnet/dotnet restore /var/task/coderunners/csharp_template/program.csproj

COPY --parents models.py coderunners/*.py ./


FROM base AS java
RUN dnf install -y java-25-amazon-corretto-devel && dnf clean all && rm -rf /var/cache/dnf
COPY --parents models.py coderunners/*.py ./


FROM base AS js
RUN dnf install -y nodejs24 && dnf clean all && rm -rf /var/cache/dnf
COPY --parents models.py coderunners/*.py ./


FROM base AS ts
RUN dnf install -y nodejs24 && dnf clean all && rm -rf /var/cache/dnf
RUN mkdir -p /var/task/typescript_runner && \
    cd /var/task/typescript_runner && \
    npm install typescript @types/node
COPY --parents models.py coderunners/*.py ./


FROM base AS dart
RUN dnf install -y unzip && dnf clean all && rm -rf /var/cache/dnf
ADD https://storage.googleapis.com/dart-archive/channels/stable/release/3.12.0/sdk/dartsdk-linux-x64-release.zip /tmp/dart-sdk.zip
RUN mkdir -p /var/dart && \
    unzip -q /tmp/dart-sdk.zip -d /var/dart && \
    rm -f /tmp/dart-sdk.zip && \
    /var/dart/dart-sdk/bin/dart --disable-analytics && \
    /var/dart/dart-sdk/bin/dart --version
COPY --parents models.py coderunners/*.py ./


FROM base AS swift
RUN dnf install -y \
    binutils \
    gcc \
    glibc-static \
    gzip \
    libbsd \
    libcurl-devel \
    libedit \
    libicu \
    libstdc++-static \
    libuuid \
    libxml2-devel \
    openssl-devel \
    tar \
    tzdata && \
    dnf clean all && rm -rf /var/cache/dnf
ADD https://download.swift.org/swift-6.3.2-release/amazonlinux2023/swift-6.3.2-RELEASE/swift-6.3.2-RELEASE-amazonlinux2023.tar.gz /tmp/swift.tar.gz
RUN set -eux; \
    tar -xzf /tmp/swift.tar.gz --directory / --strip-components=1; \
    chmod -R o+r /usr/lib/swift; \
    rm -f /tmp/swift.tar.gz; \
    swift --version
COPY --parents models.py coderunners/*.py ./


FROM base AS php
RUN dnf install -y php8.5-cli && dnf clean all && rm -rf /var/cache/dnf
COPY --parents models.py coderunners/*.py ./


FROM base AS ruby
RUN dnf install -y ruby3.4 && dnf clean all && rm -rf /var/cache/dnf
COPY --parents models.py coderunners/*.py ./


FROM base AS rust
RUN dnf install -y rust && dnf clean all && rm -rf /var/cache/dnf
COPY --parents models.py coderunners/*.py ./


FROM base AS zig
RUN dnf install -y tar xz && dnf clean all && rm -rf /var/cache/dnf
ADD https://ziglang.org/download/0.16.0/zig-x86_64-linux-0.16.0.tar.xz /tmp/zig.tar.xz
RUN mkdir -p /var/zig && \
    tar -xJf /tmp/zig.tar.xz --strip-components=1 -C /var/zig && \
    rm -f /tmp/zig.tar.xz
COPY --parents models.py coderunners/*.py ./


FROM base AS kotlin
RUN dnf install -y java-25-amazon-corretto-devel unzip && dnf clean all && rm -rf /var/cache/dnf
ADD https://github.com/JetBrains/kotlin/releases/download/v2.3.21/kotlin-compiler-2.3.21.zip /tmp/kotlin-compiler.zip
RUN mkdir -p /var/kotlin && \
    unzip -q /tmp/kotlin-compiler.zip -d /var/kotlin && \
    rm -f /tmp/kotlin-compiler.zip
COPY --parents models.py coderunners/*.py ./


FROM base AS scala
RUN dnf install -y java-25-amazon-corretto-devel gzip && dnf clean all && rm -rf /var/cache/dnf
ADD https://github.com/VirtusLab/scala-cli/releases/download/v1.14.0/scala-cli-x86_64-pc-linux-mostly-static.gz /tmp/scala-cli.gz
RUN gzip -dc /tmp/scala-cli.gz > /usr/local/bin/scala-cli && \
    chmod +x /usr/local/bin/scala-cli && \
    rm -f /tmp/scala-cli.gz
RUN mkdir -p /var/task/scala_runner/coursier-cache /tmp/scala_cache_warm && \
    printf '%s\n' '@main def main(): Unit = println("warm")' > /tmp/scala_cache_warm/main.scala && \
    COURSIER_CACHE=/var/task/scala_runner/coursier-cache \
        scala-cli --power package /tmp/scala_cache_warm/main.scala \
        --server=false --assembly --preamble=false \
        -o /tmp/scala_cache_warm/main.jar --force && \
    chmod -R a+rX /var/task/scala_runner/coursier-cache && \
    rm -rf /tmp/scala_cache_warm
COPY --parents models.py coderunners/*.py ./


FROM base AS python
COPY --parents models.py coderunners/*.py ./


FROM base AS python_ml
RUN python -m pip install --upgrade numpy pandas matplotlib scikit-learn
COPY --parents models.py coderunners/*.py ./


FROM base AS sqlite
RUN python -m pip install --upgrade pandas
COPY --parents models.py coderunners/*.py ./


FROM base AS txt
COPY --parents models.py coderunners/*.py ./
