FROM public.ecr.aws/sam/build-python3.9:latest

# Initial setup
RUN curl -sL https://rpm.nodesource.com/setup_16.x | bash -
RUN yum install -y nodejs

RUN pip install --upgrade pip
RUN pip install awslambdaric -t "${LAMBDA_TASK_ROOT}"

# Install dependencies
COPY coderunner.requirements.txt ./
RUN pip install -r coderunner.requirements.txt -t "${LAMBDA_TASK_ROOT}"

# Setup source files
COPY *.py ${LAMBDA_TASK_ROOT}/

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "app.run_code_lambda" ]
