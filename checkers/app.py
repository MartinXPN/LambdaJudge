from models import SubmissionRequest, SubmissionResult
from services import check_equality


def equality_checker_lambda(event, context):
    print('Event:', event)
    print('Context:', context)
    request = SubmissionRequest.from_dict(event)
    print('ALl the params:', request)

    assert request.problem.endswith('.zip')
    result: SubmissionResult = check_equality(request)

    return {
        'statusCode': 200,
        'body': result.to_json(),
    }
