FROM public.ecr.aws/lambda/python:3.14 as base

# Initial setup
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade awslambdaric cryptography dataclasses-json psutil

# Setup source files
COPY coderunners/*.py ${LAMBDA_TASK_ROOT}/coderunners/
COPY models.py ${LAMBDA_TASK_ROOT}/

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "coderunners.app.run_code_lambda" ]


FROM base AS c
RUN dnf install -y gcc


FROM base AS cpp
RUN dnf install -y gcc-c++ clang-tools-extra libasan


FROM base AS csharp
RUN dnf install -y tar gzip findutils libicu
ADD https://dot.net/v1/dotnet-install.sh ./dotnet-install.sh
RUN sh dotnet-install.sh --version latest
RUN mv /root/.dotnet /var/dotnet

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
    HOME=/tmp


FROM base AS java
RUN dnf install -y java-21-amazon-corretto-devel


FROM base AS js
RUN rpm -ivh https://rpm.nodesource.com/pub_16.x/nodistro/repo/nodesource-release-nodistro-1.noarch.rpm
RUN dnf install nodejs -y --setopt=nodesource-nodejs.module_hotfixes=1


FROM base AS python
# No additional dependencies needed for Python


FROM base AS python_ml
RUN python -m pip install --upgrade numpy pandas matplotlib scikit-learn


FROM base AS sqlite
RUN python -m pip install --upgrade pandas


FROM base AS txt
# No additional dependencies needed for TXT
