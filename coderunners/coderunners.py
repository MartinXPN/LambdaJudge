from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from models import Status, RunResult
from process import Process


@dataclass
class CodeRunner:
    executable_path: Path
    time_limit: float
    memory_limit_mb: int

    def run(self, program_input) -> RunResult:
        with NamedTemporaryFile('w+') as tmp:
            print(f'Saving the input to {tmp.name}')
            tmp.write(program_input)
            tmp.seek(0)

            res = Process(f'cat {tmp.name} | {self.executable_path}',
                          timeout=self.time_limit,
                          memory_limit_mb=self.memory_limit_mb).run()

        if (not res.outputs and res.errors) or res.status != Status.OK:
            print('Errs:', res.errors)
            print('Return code:', res.return_code)

        return RunResult(status=res.status, memory=res.max_rss, time=res.total_time, outputs=res.outputs)
