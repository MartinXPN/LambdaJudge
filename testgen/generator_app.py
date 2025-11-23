from models import TestGenRequest
from testgen.generator import generate_tests


def handler(event, context):
    """
    Lambda to execute code that generates tests.
    This lambda has no internet access and no permissions to access resources.
    It is run on an isolated container after which the results are stored in S3.
    """
    print('Event:', type(event), event)
    print('Context:', context)
    generator_request = TestGenRequest.from_dict(event)
    print('Generator request:', generator_request)

    results = generate_tests(generator_request)
    return results.to_json()
