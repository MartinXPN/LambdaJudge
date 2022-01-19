import json
from dataclasses import dataclass, field
from typing import List, Dict

from dataclasses_json import dataclass_json, LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CodeRunRequest:
    # Code is a mapping from filename.extension -> content (Http requests have 2MB limit)
    code: Dict[str, str]
    language: str
    memory_limit: int = 512
    time_limit: int = 5
    output_limit: float = 1
    program_inputs: List[str] = field(default_factory=list)


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
        raise ValueError(f'{language} does not have a compiler yet')

    def invoke(self, aws_lambda_client, request: CodeRunRequest):
        res = aws_lambda_client.invoke(FunctionName=self.name, Payload=request.to_json())['Payload']
        res = res.read().decode('utf-8')
        print('invocation result:', res)
        res = json.loads(res)
        return res


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
