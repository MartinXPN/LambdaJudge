from bouncer.judges import check_equality
from models import SubmissionRequest


def equality_checker_lambda(event, context):
    """
    Judge lambda that takes a request (as an API request) and returns the results
    after running the code on  run_code_lambda
    """
    print('Event:', type(event), event)
    print('Context:', context)
    request = SubmissionRequest.from_json(event['body'])
    print('ALl the params:', request)

    result = check_equality(request)
    return {
        'statusCode': 200,
        'body': result.to_json(),
    }
