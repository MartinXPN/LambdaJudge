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

    # flake8: noqa: C901
    @staticmethod
    def from_language(language: str) -> CodeRunner:
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
        if language in TsRunner.supported_standards:
            return TsRunner()
        if language in RRunner.supported_standards:
            return RRunner()
        if language in JuliaRunner.supported_standards:
            return JuliaRunner()
        if language in GoRunner.supported_standards:
            return GoRunner()
        if language in DartRunner.supported_standards:
            return DartRunner()
        if language in SwiftRunner.supported_standards:
            return SwiftRunner()
        if language in PhpRunner.supported_standards:
            return PhpRunner()
        if language in RubyRunner.supported_standards:
            return RubyRunner()
        if language in LuaRunner.supported_standards:
            return LuaRunner()
        if language in RustRunner.supported_standards:
            return RustRunner()
        if language in ZigRunner.supported_standards:
            return ZigRunner()
        if language in KotlinRunner.supported_standards:
            return KotlinRunner()
        if language in ScalaRunner.supported_standards:
            return ScalaRunner()
        if language in HaskellRunner.supported_standards:
            return HaskellRunner()
        if language in OcamlRunner.supported_standards:
            return OcamlRunner()
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
class TsRunner(CodeRunner):
    supported_standards = {'ts', 'typescript'}

    @property
    def name(self) -> str:
        return 'CodeRunnerTs'


@dataclass
class RRunner(CodeRunner):
    supported_standards = {'r'}

    @property
    def name(self) -> str:
        return 'CodeRunnerR'


@dataclass
class JuliaRunner(CodeRunner):
    supported_standards = {'julia', 'jl'}

    @property
    def name(self) -> str:
        return 'CodeRunnerJulia'


@dataclass
class GoRunner(CodeRunner):
    supported_standards = {'go', 'golang'}

    @property
    def name(self) -> str:
        return 'CodeRunnerGo'


@dataclass
class DartRunner(CodeRunner):
    supported_standards = {'dart'}

    @property
    def name(self) -> str:
        return 'CodeRunnerDart'


@dataclass
class SwiftRunner(CodeRunner):
    supported_standards = {'swift'}

    @property
    def name(self) -> str:
        return 'CodeRunnerSwift'


@dataclass
class PhpRunner(CodeRunner):
    supported_standards = {'php'}

    @property
    def name(self) -> str:
        return 'CodeRunnerPhp'


@dataclass
class RubyRunner(CodeRunner):
    supported_standards = {'ruby'}

    @property
    def name(self) -> str:
        return 'CodeRunnerRuby'


@dataclass
class LuaRunner(CodeRunner):
    supported_standards = {'lua', 'lua5.4'}

    @property
    def name(self) -> str:
        return 'CodeRunnerLua'


@dataclass
class RustRunner(CodeRunner):
    supported_standards = {'rust'}

    @property
    def name(self) -> str:
        return 'CodeRunnerRust'


@dataclass
class ZigRunner(CodeRunner):
    supported_standards = {'zig'}

    @property
    def name(self) -> str:
        return 'CodeRunnerZig'


@dataclass
class KotlinRunner(CodeRunner):
    supported_standards = {'kotlin', 'kt'}

    @property
    def name(self) -> str:
        return 'CodeRunnerKotlin'


@dataclass
class ScalaRunner(CodeRunner):
    supported_standards = {'scala', 'scala3'}

    @property
    def name(self) -> str:
        return 'CodeRunnerScala'


@dataclass
class HaskellRunner(CodeRunner):
    supported_standards = {'haskell', 'hs'}

    @property
    def name(self) -> str:
        return 'CodeRunnerHaskell'


@dataclass
class OcamlRunner(CodeRunner):
    supported_standards = {'ocaml', 'ml'}

    @property
    def name(self) -> str:
        return 'CodeRunnerOcaml'


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
