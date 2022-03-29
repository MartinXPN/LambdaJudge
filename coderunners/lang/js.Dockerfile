FROM public.ecr.aws/sam/build-python3.9:latest

# Initial setup
RUN curl -sL https://rpm.nodesource.com/setup_16.x | bash -
RUN yum install -y nodejs

COPY ./* /tmp/docker/
RUN source /tmp/docker/coderunners/build_image.sh

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "coderunners.app.run_code_lambda" ]
