FROM public.ecr.aws/lambda/python:3.13

# Initial setup
RUN pip install --upgrade pip
RUN pip install awslambdaric -t "${LAMBDA_TASK_ROOT}"

RUN python -m pip install --upgrade psutil dataclasses-json numpy scipy scikit-learn

COPY ./testgen/*.py ${LAMBDA_TASK_ROOT}/testgen/
COPY ./coderunners/process.py ${LAMBDA_TASK_ROOT}/coderunners/
COPY ./models.py ${LAMBDA_TASK_ROOT}/


# Run the lambda function handler
ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "testgen.generator.handler" ]
