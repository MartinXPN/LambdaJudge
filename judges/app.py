from models import SubmissionRequest
from services import check_equality


def equality_checker_lambda(event, context):
    print('Event:', type(event), event)
    print('Context:', context)
    request = SubmissionRequest.from_json(event['body'])
    print('ALl the params:', request)

    result = check_equality(request)
    return {
        'statusCode': 200,
        'body': result.to_json(),
    }
