from models import CodeRunRequest
from services import run_code


def run_code_lambda(event, context):
    print('Event:', type(event), event)
    print('Context:', context)

    # TODO: Handle pickled requests as well
    request = CodeRunRequest.from_dict(event)
    print('ALl the params:', request)

    result = run_code(**request.__dict__)
    print('result:', result)
    return result.to_json()
