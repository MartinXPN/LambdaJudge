FROM public.ecr.aws/sam/build-python3.9:latest

## Initial setup

COPY ./bouncer ${LAMBDA_TASK_ROOT}/
COPY ./models.py ${LAMBDA_TASK_ROOT}/
COPY ./requirements-bouncer.txt ${LAMBDA_TASK_ROOT}/

RUN pip install --upgrade pip
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements-bouncer.txt -t "${LAMBDA_TASK_ROOT}"

# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "bouncer.app.equality_checker_lambda" ]
