from dataclasses import dataclass
from pathlib import Path

from models import Status, RunResult
from process import Process


@dataclass
class CodeRunner:
    executable_path: Path
    time_limit: float
    memory_limit_mb: int
    output_limit_mb: float

    def run(self, program_input: str) -> RunResult:
        res = Process(
            f'{self.executable_path}',
            timeout=self.time_limit, memory_limit_mb=self.memory_limit_mb, output_limit_mb=self.output_limit_mb
        ).run(program_input)

        if (not res.outputs and res.errors) or res.status != Status.OK:
            print(f'Errs: {res.errors}')
            print(f'Return code: {res.return_code}, status: {res.status}')

        return RunResult(status=res.status, memory=res.max_rss, time=res.total_time,
                         return_code=res.return_code,
                         outputs=res.outputs, errors=res.errors)
