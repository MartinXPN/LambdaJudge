from pathlib import Path

from models import TestGenRequest, TestGenResponse


def generate_tests(request: TestGenRequest) -> tuple[TestGenResponse, Path]:
    zip_path = Path('/tmp/') / 'tests.zip'
    return TestGenResponse(status='success', message=''), zip_path
