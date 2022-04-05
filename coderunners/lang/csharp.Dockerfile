FROM public.ecr.aws/sam/build-python3.9:latest

# Initial setup
# RUN yum install -y wget
# RUN wget https://dot.net/v1/dotnet-install.sh

ADD https://dot.net/v1/dotnet-install.sh ./dotnet-install.sh
RUN sh dotnet-install.sh -c 6.0
RUN mv /root/.dotnet /var/dotnet

ENV \
    # Export .NET version as environment variable
    # DOTNET_VERSION=$ASPNET_VERSION \
    # Enable detection of running in a container
    DOTNET_RUNNING_IN_CONTAINER=true \
    # Lambda is opinionated about installing tooling under /var
    DOTNET_CLI_HOME=/tmp \
    # Don't display welcome message on first run
    DOTNET_NOLOGO=true \
    # Disable Microsoft's telemetry collection
    DOTNET_CLI_TELEMETRY_OPTOUT=true \
    HOME=/tmp

RUN pip install --upgrade pip
RUN pip install "awslambdaric>=2,<3" -t "${LAMBDA_TASK_ROOT}"

# Install dependencies
COPY coderunners/requirements.txt ./
RUN pip install -r requirements.txt -t "${LAMBDA_TASK_ROOT}"

# Setup source files
COPY coderunners/*.py ${LAMBDA_TASK_ROOT}/coderunners/
COPY models.py ${LAMBDA_TASK_ROOT}/

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "coderunners.app.run_code_lambda" ]
