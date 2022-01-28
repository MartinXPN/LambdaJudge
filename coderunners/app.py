from models import SubmissionRequest, SubmissionResult
from services import check_code


def run_code_lambda(event, context):
    print('Event:', type(event), event)
    print('Context:', context)
    request = SubmissionRequest.from_dict(event)
    print('ALl the params:', request)

    results: SubmissionResult = check_code(**request.__dict__)
    return results.to_json()
