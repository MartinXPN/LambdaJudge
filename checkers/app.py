from models import SubmissionRequest, SubmissionResult
from services import check_equality


def equality_checker_lambda(event, context):
    print('Event:', event)
    print('Context:', context)
    request = SubmissionRequest.from_dict(event)
    print('ALl the params:', request)

    assert request.problem.endswith('.zip')
    result: SubmissionResult = check_equality(
        problem=request.problem, submission=request.submission, language=request.language,
        memory_limit=request.memory_limit, time_limit=request.time_limit,
        return_outputs=request.return_outputs, return_compile_outputs=request.return_compile_outputs,
        stop_on_first_fail=request.stop_on_first_fail)

    return {
        'statusCode': 200,
        'body': result.to_json(),
    }
