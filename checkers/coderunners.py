from dataclasses import dataclass


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
