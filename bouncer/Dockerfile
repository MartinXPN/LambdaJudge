FROM public.ecr.aws/lambda/python:3.13

# Initial setup
RUN pip install --upgrade pip
RUN pip install awslambdaric -t "${LAMBDA_TASK_ROOT}"

RUN python -m pip install --upgrade boto3 dataclasses-json requests

COPY ./bouncer/*.py ${LAMBDA_TASK_ROOT}/bouncer/
COPY ./models.py ${LAMBDA_TASK_ROOT}/


# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "bouncer.app.bouncer_lambda_handler" ]
