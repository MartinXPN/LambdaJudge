FROM public.ecr.aws/lambda/python:3.14
WORKDIR ${LAMBDA_TASK_ROOT}

# Initial setup
RUN python -m pip install --upgrade boto3 dataclasses-json requests
COPY --parents models.py bouncer/*.py ./

# Run the lambda function handler
CMD [ "bouncer.app.bouncer_lambda_handler" ]
