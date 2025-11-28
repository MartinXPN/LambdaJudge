FROM public.ecr.aws/lambda/python:3.14

# Initial setup
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade awslambdaric boto3 dataclasses-json psutil numpy scipy scikit-learn

COPY testgen/*.py ${LAMBDA_TASK_ROOT}/testgen/
COPY models.py ${LAMBDA_TASK_ROOT}/
COPY coderunners/process.py ${LAMBDA_TASK_ROOT}/coderunners/
COPY coderunners/util.py ${LAMBDA_TASK_ROOT}/coderunners/

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "testgen.generator_app.handler" ]
