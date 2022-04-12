import os


class PrivateTestSummarizerException(Exception):
    pass


class PrivateTestSummarizer:

    TABLENAME = os.getenv('DYNAMODB_TABLE_NAME', 'private-tests')

    def __init__(self, dynamodb):
        self.table = dynamodb.Table(self.TABLENAME)

    def write(self, problem_id: str, tests: list[dict[str, str]]):
        response = self.table.put_item(Item={'id': problem_id, 'count': len(tests), 'tests': tests})
        if response['ResponseMetadata']['HTTPStatusCode'] not in range(200, 300):
            raise PrivateTestSummarizerException('Cannot summarize item', response)
