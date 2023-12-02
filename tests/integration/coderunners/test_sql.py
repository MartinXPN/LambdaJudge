from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestSQLSubmissions:

    def test_echo(self):
        test_cases = [
            TestCase(
                input=dedent('''
                    -- Initialization script goes here
                '''),
                target=dedent('''
                    'hello world'
                    hello world
                ''').strip()),
        ]
        request = SubmissionRequest(test_cases=test_cases, return_outputs=True, language='SQL', code={
            'main.sql': dedent('''
                SELECT 'hello world'
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.overall.score == 100
        assert len(res.test_results) == 1
        assert res.test_results[0].status == Status.OK

    def test_create_table(self):
        test_cases = [
            TestCase(
                input=dedent('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL
                    );
                '''),
                target=dedent('''
                    COUNT(*)
                    3
                ''').strip(),
                input_files={
                    'users': dedent('''
                        id,name
                        1,John
                        2,Jane
                        3,Martin
                    ''').strip(),
                },
                target_files={
                    'users': dedent('''
                        id,name
                        1,John
                        2,Jane
                        3,Martin
                    ''').strip(),
                }),
        ]
        request = SubmissionRequest(test_cases=test_cases, return_outputs=True, language='SQL', code={
            'main.sql': dedent('''
                SELECT COUNT(*) FROM users;
            ''').strip(),
        }, comparison_mode='token')
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.overall.score == 100
        assert len(res.test_results) == 1
        assert res.test_results[0].status == Status.OK

    def test_insert(self):
        test_cases = [
            TestCase(
                input=dedent('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL
                    );
                '''),
                target='',
                input_files={
                    'users': dedent('''
                        id,name
                        1,John
                        2,Jane
                        3,Martin
                    ''').strip(),
                },
                target_files={
                    'users': dedent('''
                        id,name
                        1,John
                        2,Jane
                        3,Martin
                        4,Jack
                    ''').strip(),
                }),
        ]
        request = SubmissionRequest(test_cases=test_cases, return_outputs=True, language='SQL', code={
            'main.sql': dedent('''
                INSERT INTO users (id, name) VALUES (4, 'Jack');
            ''').strip(),
        }, comparison_mode='token')
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.overall.score == 100
        assert len(res.test_results) == 1
        assert res.test_results[0].status == Status.OK

    def test_invalid_query(self):
        test_cases = [
            TestCase(
                input=dedent('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL
                    );
                '''),
                target='',
                input_files={
                    'users': dedent('''
                        id,name
                        1,John
                        2,Jane
                        3,Martin
                    ''').strip(),
                },
                target_files={
                    'users': dedent('''
                        id,name
                        1,John
                        2,Jane
                        3,Martin
                    ''').strip(),
                }),
        ]
        request = SubmissionRequest(test_cases=test_cases, return_outputs=True, language='SQL', code={
            # Command should result in an error
            'main.sql': dedent('''
                SELECT * FROM random_table;
            ''').strip(),
        }, comparison_mode='token')
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.RUNTIME_ERROR
        assert res.overall.score == 0
        assert len(res.test_results) == 1
        assert res.test_results[0].status == Status.RUNTIME_ERROR
