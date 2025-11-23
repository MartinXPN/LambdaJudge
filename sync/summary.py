import os
from typing import overload

from models import TestCase


class SummaryWriteError(Exception):
    pass


class SummaryTable:
    TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'private-tests')

    def __init__(self, dynamodb):
        self.table = dynamodb.Table(self.TABLE_NAME)

    def log_error(self, problem_id: str, message: str) -> None:
        self.table.put_item(Item={
            'id': problem_id,
            'status': 'error',
            'message': message,
        })

    def log_start(self, problem_id: str) -> None:
        self.table.put_item(Item={
            'id': problem_id,
            'status': 'in_progress',
            'message': '',
        })

    def write(self, problem_id: str, tests: list[TestCase]) -> None:
        response = self.table.put_item(Item={
            'id': problem_id,
            'count': len(tests),
            'tests': [t.to_dict() for t in tests],
            'status': 'success',
            'message': '',
        })
        if response['ResponseMetadata']['HTTPStatusCode'] not in range(200, 300):
            self.log_error(problem_id, 'Could not summarize the tests')
            raise SummaryWriteError('Could not summarize the tests', response)


@overload
def truncate(tests: list[TestCase], max_len: int) -> list[TestCase]:
    ...


@overload
def truncate(test: TestCase, max_len: int) -> TestCase:
    ...


def truncate(x, max_len: int = 100):
    if isinstance(x, TestCase):
        return TestCase(
            input=x.input[: max_len],
            target=x.target[: max_len],
            input_files={filename: content[: max_len] for filename, content in x.input_files.items()}
            if x.input_files is not None else None,
            target_files={filename: content[: max_len] for filename, content in x.target_files.items()}
            if x.target_files is not None else None,
            input_assets={filename: content[: max_len] for filename, content in x.input_assets.items()}
            if x.input_assets is not None else None,
            target_assets={filename: content[: max_len] for filename, content in x.target_assets.items()}
            if x.target_assets is not None else None,
        )

    if isinstance(x, list):
        return [truncate(t, max_len) for t in x]

    raise ValueError('Not supported type for truncation')
