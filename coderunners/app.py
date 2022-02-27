from models import SubmissionRequest, SubmissionResult


def run_code_lambda(event, context):
    """
    Lambda to execute code.
    This lambda has no internet access and no permissions to access resources
    It is run on an isolated container after which the results are returned to the "caller" function
    """
    from services import check_code
    print('Event:', type(event), event)
    print('Context:', context)
    request = SubmissionRequest.from_dict(event)
    print('ALl the params:', request)

    results: SubmissionResult = check_code(**request.__dict__)
    return results.to_json()


def equality_checker_lambda(event, context):
    """
    Judge lambda that takes a request (as an API request) and returns the results
    after running the code on  run_code_lambda
    """
    from judges import check_equality
    print('Event:', type(event), event)
    print('Context:', context)
    request = SubmissionRequest.from_json(event['body'])
    print('ALl the params:', request)

    result = check_equality(request)
    return {
        'statusCode': 200,
        'body': result.to_json(),
    }
