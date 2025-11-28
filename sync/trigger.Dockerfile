FROM public.ecr.aws/lambda/python:3.14

# Initial setup
RUN pip install --upgrade pip
RUN pip install awslambdaric -t "${LAMBDA_TASK_ROOT}"

RUN python -m pip install --upgrade boto3 dataclasses-json

COPY ./sync/*.py ${LAMBDA_TASK_ROOT}/sync/
COPY ./models.py ${LAMBDA_TASK_ROOT}/


# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "sync.trigger_app.handler" ]
