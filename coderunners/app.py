from coderunners.services import EqualityChecker
from models import SubmissionResult


def run_code_lambda(event, context):
    """
    Lambda to execute code.
    This lambda has no internet access and no permissions to access resources
    It is run on an isolated container after which the results are returned to the "caller" function
    """
    print('Event:', type(event), event)
    print('Context:', context)
    checker = EqualityChecker.from_dict(event)
    print('Checker:', checker)

    results: SubmissionResult = checker.check()
    return results.to_json()
