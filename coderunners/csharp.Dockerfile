FROM public.ecr.aws/sam/build-python3.9:latest

## Initial setup
RUN yum install -y wget
RUN wget https://dot.net/v1/dotnet-install.sh
RUN sh dotnet-install.sh -c 6.0

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
