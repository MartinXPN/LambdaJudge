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
# 5. Set HOME to a writable directory
ENV \
    DOTNET_RUNNING_IN_CONTAINER=true \
    DOTNET_CLI_HOME=/tmp \
    DOTNET_NOLOGO=true \
    DOTNET_CLI_TELEMETRY_OPTOUT=true \
    DOTNET_SKIP_WORKLOAD_INTEGRITY_CHECK=true \
    DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE=true \
    HOME=/tmp

COPY --parents models.py coderunners/*.py ./

# Cache the project template and dependencies to speed up cold starts
RUN /var/dotnet/dotnet new console --force --name program --output /var/task/coderunners/csharp_template && \
    rm /var/task/coderunners/csharp_template/Program.cs && \
    mkdir -p /var/task/coderunners/csharp_template/Submission && \
    printf '%s\n' 'internal static class Program { private static void Main() { } }' \
      > /var/task/coderunners/csharp_template/Submission/main.cs && \
    /var/dotnet/dotnet restore /var/task/coderunners/csharp_template/program.csproj


FROM base AS java
RUN dnf install -y java-25-amazon-corretto-devel && dnf clean all && rm -rf /var/cache/dnf
COPY --parents models.py coderunners/*.py ./


FROM base AS js
RUN dnf install -y nodejs24 && dnf clean all && rm -rf /var/cache/dnf
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
