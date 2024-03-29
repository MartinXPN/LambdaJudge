import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from models import SubmissionRequest, SubmissionResult


class CodeRunner(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """ The name defined here should match the name in the SAM template.yaml """
        ...

    @staticmethod
    def from_language(language: str) -> 'CodeRunner':
        language = language.lower()
        if language in TxtRunner.supported_standards:
            return TxtRunner()
        if language in CRunner.supported_standards:
            return CRunner()
        if language in CppRunner.supported_standards:
            return CppRunner()
        if language in PythonRunner.supported_standards:
            return PythonRunner()
        if language in PythonMLRunner.supported_standards:
            return PythonMLRunner()
        if language in CSharpRunner.supported_standards:
            return CSharpRunner()
        if language in JsRunner.supported_standards:
            return JsRunner()
        if language in JavaRunner.supported_standards:
            return JavaRunner()
        if language in SQLiteRunner.supported_standards:
            return SQLiteRunner()
        raise ValueError(f'{language} does not have a compiler yet')

    def invoke(self, aws_lambda_client, request: SubmissionRequest) -> SubmissionResult:
        res = aws_lambda_client.invoke(FunctionName=self.name, Payload=request.to_json())['Payload']
        res = res.read().decode('utf-8')
        res = json.loads(res)
        print('invocation result:', res)
        return SubmissionResult.from_json(res)


@dataclass
class TxtRunner(CodeRunner):
    supported_standards = {'txt', 'text'}

    @property
    def name(self) -> str:
        return 'CodeRunnerTxt'


@dataclass
class CRunner(CodeRunner):
    supported_standards = {'c', 'c11', 'c17', 'c23'}

    @property
    def name(self) -> str:
        return 'CodeRunnerC'


@dataclass
class CppRunner(CodeRunner):
    supported_standards = {'c++', 'c++11', 'c++14', 'c++17', 'c++20', 'c++23'}

    @property
    def name(self) -> str:
        return 'CodeRunnerCpp'


@dataclass
class PythonRunner(CodeRunner):
    supported_standards = {'python', 'python3'}

    @property
    def name(self) -> str:
        return 'CodeRunnerPython'


@dataclass
class PythonMLRunner(CodeRunner):
    supported_standards = {'pythonml'}

    @property
    def name(self) -> str:
        return 'CodeRunnerPythonML'


@dataclass
class CSharpRunner(CodeRunner):
    supported_standards = {'c#'}

    @property
    def name(self) -> str:
        return 'CodeRunnerCSharp'


@dataclass
class JsRunner(CodeRunner):
    supported_standards = {'js'}

    @property
    def name(self) -> str:
        return 'CodeRunnerJs'


@dataclass
class JavaRunner(CodeRunner):
    supported_standards = {'java'}

    @property
    def name(self) -> str:
        return 'CodeRunnerJava'


@dataclass
class SQLiteRunner(CodeRunner):
    supported_standards = {'sql', 'sqlite'}

    @property
    def name(self) -> str:
        return 'CodeRunnerSQLite'
