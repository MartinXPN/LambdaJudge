import os


class PrivateTestLoggerException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PrivateTestLogger:

    TABLENAME = os.getenv('DYNAMODB_TABLE_NAME', 'private-tests')

    def __init__(self, dynamodb):
        self.table = dynamodb.Table(self.TABLENAME)

    def log(self, problem_id: str, tests: list[dict[str, str]]):
        response = self.table.put_item(Item={'id': problem_id, 'count': len(tests),
                                       'tests': self.truncated_tests(tests)})
        if response['ResponseMetadata']['HTTPStatusCode'] not in range(200, 300):
            raise PrivateTestLoggerException('Cannot log item', response)

    @classmethod
    def truncated_tests(cls, tests):
        return [cls.truncated_test(test) for test in tests]

    @classmethod
    def truncated_test(cls, test):
        return {'input': cls.truncated(test['input']), 'target': cls.truncated(test['target'])}

    @classmethod
    def truncated(cls, value: str):
        return value[:min(len(value), 100)]
