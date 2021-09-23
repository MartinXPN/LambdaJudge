from dataclasses import dataclass
from pathlib import Path

from models import Status, TestResult
from process import Process


@dataclass
class CodeRunner:
    executable_path: Path
    time_limit: float
    memory_limit_mb: int

    def run(self, test_input) -> TestResult:
        res = Process(f'echo "{test_input}" | {self.executable_path}',
                      timeout=self.time_limit,
                      memory_limit_mb=self.memory_limit_mb).run()

        if (not res.outputs and res.errors) or res.status != Status.OK:
            print('Errs:', res.errors)
            print('Return code:', res.return_code)

        return TestResult(status=res.status, memory=res.max_rss, time=res.total_time, outputs=res.outputs)
