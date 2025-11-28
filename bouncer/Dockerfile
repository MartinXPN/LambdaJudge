FROM public.ecr.aws/lambda/python:3.14

# Initial setup
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade awslambdaric boto3 dataclasses-json requests

COPY bouncer/*.py ${LAMBDA_TASK_ROOT}/bouncer/
COPY models.py ${LAMBDA_TASK_ROOT}/


# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "bouncer.app.bouncer_lambda_handler" ]
