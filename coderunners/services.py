from pathlib import Path
from typing import Dict, List, Tuple, Optional

from coderunners import CodeRunner
from compilers import Compiler
from models import Status, RunResult
from process import Process

ROOT = Path('/tmp/')


def save_code(save_dir: Path, code: Dict[str, str]) -> List[Path]:
    saved_paths: List[Path] = []
    for filename, content in code.items():
        path = save_dir / filename
        saved_paths.append(path)
        with open(path, 'w') as f:
            f.write(content)

    return saved_paths


def run_code(code: Dict[str, str], language: str, memory_limit: int, time_limit: int,
             program_inputs: List[str]) -> Tuple[RunResult, Optional[List[RunResult]]]:
    Process('rm -rf /tmp/*', timeout=5, memory_limit_mb=512).run()  # Avoid having no space left on device issues
    submission_path = save_code(save_dir=ROOT, code=code)[0]        # Currently we only support single-file submissions

    # Compile and prepare the executable
    compiler = Compiler.from_language(language=language)
    executable_path, compile_res = compiler.compile(submission_path=submission_path)
    # Compile error
    if compile_res.errors:
        print('Compile error:', compile_res)
        return RunResult(status=Status.COMPILATION_ERROR, memory=compile_res.max_rss, time=0,
                         outputs=compile_res.outputs, errors=compile_res.errors), None

    compile_res = RunResult(status=Status.OK, memory=compile_res.max_rss, time=compile_res.total_time,
                            outputs=compile_res.outputs)
    code_runner = CodeRunner(executable_path=executable_path, time_limit=time_limit, memory_limit_mb=memory_limit)
    run_results = []
    for program_input in program_inputs:
        res = code_runner.run(program_input)
        run_results.append(res)
        if res.status != Status.OK:
            break
    print('Run results:', run_results)

    return compile_res, run_results
