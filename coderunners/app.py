import pickle

from models import CodeRunRequest, RunResult
from services import run_code


def run_code_lambda(event, context):
    print('Event:', type(event), event)
    print('Context:', context)

    if isinstance(event, bytes):
        event = pickle.loads(event)
    request = CodeRunRequest.from_dict(event)
    print('ALl the params:', request)

    compile_res, run_results = run_code(**request.__dict__)
    return {
        'compilation': compile_res.to_json() if compile_res else None,
        'results': RunResult.schema().dumps(run_results, many=True) if run_results else None,
    }
