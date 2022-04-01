FROM public.ecr.aws/sam/build-python3.9:latest

## Initial setup
RUN yum install -y gcc-c++

RUN pip install --upgrade pip
RUN pip install awslambdaric -t "${LAMBDA_TASK_ROOT}"

# Install dependencies
COPY requirements-coderunners.txt ./
RUN pip install -r requirements-coderunners.txt -t "${LAMBDA_TASK_ROOT}"

# Setup source files
COPY coderunners/*.py ${LAMBDA_TASK_ROOT}/coderunners/
COPY models.py ${LAMBDA_TASK_ROOT}/
COPY errors.py ${LAMBDA_TASK_ROOT}/

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "coderunners.app.run_code_lambda" ]
