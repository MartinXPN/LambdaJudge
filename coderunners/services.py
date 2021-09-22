from typing import Dict, List

from models import CodeRunResult


def run_code(code: Dict[str, str], language: str, memory_limit: int, time_limit: int,
             test_inputs: List[str],
             return_outputs: bool, return_compile_outputs: bool) -> CodeRunResult:
    return CodeRunResult(memory=[], time=[], outputs=[], compile_outputs='Yyoyo')
