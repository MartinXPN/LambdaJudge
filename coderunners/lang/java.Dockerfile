FROM public.ecr.aws/sam/build-python3.9:latest

RUN yum install -y java-17-amazon-corretto-devel

COPY ./* /tmp/docker/
RUN source /tmp/docker/coderunners/build_image.sh

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "coderunners.app.run_code_lambda" ]
