# syntax=docker/dockerfile:1
FROM public.ecr.aws/lambda/python:3.14
WORKDIR ${LAMBDA_TASK_ROOT}

# Initial setup
RUN python -m pip install --upgrade boto3 dataclasses-json
COPY --parents models.py sync/*.py ./

# Run the lambda function handler
CMD [ "sync.trigger_app.handler" ]
