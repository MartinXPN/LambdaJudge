import uuid

import boto3

from sync.private_test_logger import PrivateTestLogger


def main():
    session = boto3.session.Session(profile_name='profound_academy')
    db = session.resource('dynamodb')

    logger = PrivateTestLogger(db)
    key = str(uuid.uuid4())

    tests = [
        {"input": "abc", "target": "cba"},
        {"input": "def", "target": "fed"},
    ]

    logger.log(problem_id=key, tests=tests)
    print('Key:', key)


if __name__ == '__main__':
    main()
