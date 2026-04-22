FROM public.ecr.aws/lambda/python:3.14
WORKDIR ${LAMBDA_TASK_ROOT}

# Initial setup
RUN python -m pip install --upgrade boto3 dataclasses-json psutil numpy scipy scikit-learn
COPY --parents models.py testgen/*.py coderunners/process.py coderunners/util.py ./

# Run the lambda function handler
CMD [ "testgen.generator_app.handler" ]
