FROM public.ecr.aws/lambda/python:3.14

# Initial setup
RUN pip install --upgrade pip
RUN pip install awslambdaric -t "${LAMBDA_TASK_ROOT}"

RUN python -m pip install --upgrade boto3 dataclasses-json requests

COPY ./testgen/*.py ${LAMBDA_TASK_ROOT}/testgen/
COPY ./models.py ${LAMBDA_TASK_ROOT}/
COPY ./sync/summary.py ${LAMBDA_TASK_ROOT}/sync/


# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "testgen.bouncer_app.handler" ]
