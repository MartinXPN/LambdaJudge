FROM public.ecr.aws/lambda/python:3.14

# Initial setup
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade awslambdaric boto3 cryptography dataclasses-json

COPY sync/*.py ${LAMBDA_TASK_ROOT}/sync/
COPY models.py ${LAMBDA_TASK_ROOT}/


# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "sync.sync_app.handler" ]
