FROM public.ecr.aws/sam/build-python3.9:latest

## Initial setup
RUN yum install -y gcc-c++
COPY ./ /tmp/docker/
RUN source /tmp/docker/coderunners/build_image.sh

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "coderunners.app.run_code_lambda" ]
