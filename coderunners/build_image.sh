pip install --upgrade pip
pip install -r /tmp/docker/requirements-coderunner.txt -t "${LAMBDA_TASK_ROOT}"
mkdir ${LAMBDA_TASK_ROOT}/coderunners
cp /tmp/docker/coderunners/*.py ${LAMBDA_TASK_ROOT}/coderunners/
cp /tmp/docker/models.py ${LAMBDA_TASK_ROOT}/
cp /tmp/docker/errors.py ${LAMBDA_TASK_ROOT}/
rm -rf /tmp/docker
