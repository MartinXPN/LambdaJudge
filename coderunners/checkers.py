import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Optional

from coderunners.process import Process
from coderunners.util import is_float, save_code
from models import Status


class Checker(ABC):
    @abstractmethod
    def check(
        self, inputs: str, output: str, target: str,
        code: dict[str, str],
        input_files: Optional[dict[str, str]] = None,
        output_files: Optional[dict[str, str]] = None,
        target_files: Optional[dict[str, str]] = None,
        input_assets: Optional[dict[str, bytes]] = None,
        output_assets: Optional[dict[str, bytes]] = None,
        target_assets: Optional[dict[str, bytes]] = None,
    ) -> tuple[Status, float, Optional[str]]:
        """
        Check if the program behaved correctly and return the verdict
        :param inputs: all the input of the program
        :param output: the output of the submitted program
        :param target: what the output should be according to the precalculated test
        :param code: mapping {filename: content} of the submitted code
        :param input_files: files generated before running the program
        :param output_files: files created by the program (with their content)
        :param target_files: expected files with their content by the end of the program working
        :param input_assets: binary files generated before running the program
        :param output_assets: binary files created by the program
        :param target_assets: expected binary files with their content by the end of the program working
        :return: [verdict: Status, score: float 0 to 100, message: str]
        """
        ...

    @staticmethod
    def from_mode(mode: str,
                  float_precision: Optional[float] = None, delimiter: Optional[str] = None,
                  executable_path: Optional[Path] = None) -> 'Checker':
        if mode == 'whole':
            return WholeEquality()
        if mode == 'token':
            assert float_precision is not None
            return TokenEquality(float_precision=float_precision, delimiter=delimiter)
        if mode == 'custom':
            assert executable_path is not None
            return CustomChecker(executable_path=executable_path)
        raise ValueError(f'{mode} comparison mode is not implemented yet')


class WholeEquality(Checker):
    def check(
        self, inputs, output, target, code,
        input_files=None, output_files=None, target_files=None,
        input_assets=None, output_assets=None, target_assets=None,
    ) -> tuple[Status, float, Optional[str]]:
        files_match = [output_files[file].strip() == target_files[file].strip()
                       if file in output_files else False
                       for file in (target_files or {}).keys()]
        assets_match = [output_assets[file] == target_assets[file] for file in (target_assets or {}).keys()]

        if output.strip() == target.strip() and all(files_match) and all(assets_match):
            return Status.OK, 100, None
        return Status.WA, 0, None


@dataclass
class TokenEquality(Checker):
    float_precision: float = 1e-5
    delimiter: Optional[str] = None

    def is_correct(self, output: str, target: str) -> bool:
        output = output.strip().split(self.delimiter)
        target = target.strip().split(self.delimiter)
        if len(output) != len(target):
            print(f'Lengths different: out({len(output)}) target({len(target)})')
            return False

        for i, (o, t) in enumerate(zip(output, target)):
            if o.strip().lower() == t.strip().lower() and o.strip().lower() in {'nan', 'inf'}:
                continue
            if is_float(o) and is_float(t):
                diff = abs(float(o) - float(t))
                if math.isnan(diff) or diff > self.float_precision:
                    print(f'#{i} Numbers different: out({o}) target({t}) => {diff}')
                    return False
            elif o.strip() != t.strip():
                print(f'#{i} Not equal: out({o}) target({t})')
                return False

        return True

    def check(
        self, inputs, output, target, code,
        input_files=None, output_files=None, target_files=None,
        input_assets=None, output_assets=None, target_assets=None,
    ) -> tuple[Status, float, Optional[str]]:
        files_match = [self.is_correct(output_files[file], target_files[file])
                       if file in output_files else False
                       for file in (target_files or {}).keys()]
        assets_match = [output_assets[file] == target_assets[file] for file in (target_assets or {}).keys()]

        if self.is_correct(output, target) and all(files_match) and all(assets_match):
            return Status.OK, 100, None
        return Status.WA, 0, None


@dataclass
class CustomChecker(Checker):
    executable_path: Path

    def check(
        self, inputs, output, target, code,
        input_files=None, output_files=None, target_files=None,
        input_assets=None, output_assets=None, target_assets=None,
    ) -> tuple[Status, float, Optional[str]]:
        # TODO: How to support files and assets for custom checkers?
        with NamedTemporaryFile('w') as inf, NamedTemporaryFile('w') as ouf, NamedTemporaryFile('w') as tg, \
                TemporaryDirectory() as code_dir:
            code_dir = Path(code_dir)
            save_code(save_dir=code_dir, code=code)
            inf.write(inputs)
            ouf.write(output)
            tg.write(target)
            inf.flush()
            ouf.flush()
            tg.flush()

            res = Process(
                f'{self.executable_path} {inf.name} {ouf.name} {tg.name} {code_dir.resolve()}',
                timeout=1, memory_limit_mb=512, output_limit_mb=1,
            ).run()

        if res.status != Status.OK:
            return res.status, 0, f'Checker failed with: {res.message}, having errors: {res.errors}'

        outputs = res.outputs.split('\n', maxsplit=2)
        if len(outputs) < 2:
            return (Status.RUNTIME_ERROR, 0,
                    'Checker failed to produce status and score (each should be on separate lines)')
        if len(outputs) == 2:
            status, score, message = outputs[0], outputs[1], None
        else:
            status, score, message = outputs

        if not is_float(score):
            return Status.RUNTIME_ERROR, 0, 'Checker did not produce a valid score value'
        score = float(score)

        try:
            status = Status(status)
        except ValueError:
            return Status.RUNTIME_ERROR, 0, 'Checker did not produce a valid status'

        return status, score, message
