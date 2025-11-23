from models import TestGenRequest, TestGenResponse


def generate_tests(request: TestGenRequest) -> TestGenResponse:
    ...
    return TestGenResponse(status='success', message='')
