FROM public.ecr.aws/sam/build-python3.9:latest

# Initial setup
RUN yum install -y wget
RUN wget https://dot.net/v1/dotnet-install.sh
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

COPY ./ /tmp/docker/
RUN source /tmp/docker/coderunners/build_image.sh

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "coderunners.app.run_code_lambda" ]
