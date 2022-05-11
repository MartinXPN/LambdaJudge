import os
from typing import overload


class SummaryWriteError(Exception):
    pass


class SummaryTable:
    TABLENAME = os.getenv('DYNAMODB_TABLE_NAME', 'private-tests')

    def __init__(self, dynamodb):
        self.table = dynamodb.Table(self.TABLENAME)

    def write(self, problem_id: str, tests: list[dict[str, str]]) -> None:
        response = self.table.put_item(Item={
            'id': problem_id,
            'count': len(tests),
            'tests': tests,
        })
        if response['ResponseMetadata']['HTTPStatusCode'] not in range(200, 300):
            raise SummaryWriteError('Cannot summarize item', response)


@overload
def truncate(tests: list[dict[str, str]], max_len: int) -> list[dict[str, str]]:
    ...


@overload
def truncate(test: dict[str, str], max_len: int) -> dict[str, str]:
    ...


def truncate(x, max_len: int = 100):
    if isinstance(x, dict):
        return {
            'input': x['input'][: max_len],
            'target': x['target'][: max_len],
        }

    if isinstance(x, list):
        return [truncate(t, max_len) for t in x]

    raise ValueError('Not supported type for truncation')
