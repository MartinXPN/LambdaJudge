import json
from dataclasses import dataclass

from models import SubmissionRequest, SubmissionResult


class CodeRunner:
    @property
    def name(self) -> str:
        """ The name defined here should match the name in the SAM template.yaml """
        raise NotImplementedError

    @staticmethod
    def from_language(language: str) -> 'CodeRunner':
        language = language.lower()
        if language in CppRunner.supported_standards:
            return CppRunner()
        if language in PythonRunner.supported_standards:
            return PythonRunner()
        if language in CSharpRunner.supported_standards:
            return CSharpRunner()
        raise ValueError(f'{language} does not have a compiler yet')

    def invoke(self, aws_lambda_client, request: SubmissionRequest) -> SubmissionResult:
        res = aws_lambda_client.invoke(FunctionName=self.name, Payload=request.to_json())['Payload']
        res = res.read().decode('utf-8')
        res = json.loads(res)
        print('invocation result:', res)
        return SubmissionResult.from_json(res)


@dataclass
class CppRunner(CodeRunner):
    supported_standards = {'c++11', 'c++14', 'c++17', 'c++20'}

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
class CSharpRunner(CodeRunner):
    supported_standards = {'c#'}

    @property
    def name(self) -> str:
        return 'CodeRunnerCSharp'
