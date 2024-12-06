FROM public.ecr.aws/lambda/python:3.13

# Initial setup
RUN dnf install -y gcc-c++ clang-tools-extra libasan

RUN pip install --upgrade pip
RUN pip install awslambdaric -t "${LAMBDA_TASK_ROOT}"

# Install dependencies
COPY coderunners/requirements.txt ./
RUN pip install -r requirements.txt -t "${LAMBDA_TASK_ROOT}"

# Setup source files
COPY coderunners/*.py ${LAMBDA_TASK_ROOT}/coderunners/
COPY models.py ${LAMBDA_TASK_ROOT}/

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "coderunners.app.run_code_lambda" ]
