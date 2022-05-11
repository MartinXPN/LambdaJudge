FROM public.ecr.aws/sam/build-python3.9:latest

# Initial setup
RUN pip install --upgrade pip
RUN pip install awslambdaric -t "${LAMBDA_TASK_ROOT}"

COPY ./bouncer/requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt -t "${LAMBDA_TASK_ROOT}"

COPY ./bouncer/*.py ${LAMBDA_TASK_ROOT}/bouncer/
COPY ./models.py ${LAMBDA_TASK_ROOT}/


# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "bouncer.app.bouncer_lambda_handler" ]
