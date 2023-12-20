from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from coderunners.process import Process
from models import RunResult, Status


class Linter(ABC):
    @abstractmethod
    def lint(self, submission_paths: list[Path]) -> RunResult:
        ...

    @staticmethod
    def from_language(language: str) -> 'Linter':
        language = language.lower()
        if language in CppLinter.supported_standards:
            return CppLinter(language_standard=language)
        raise ValueError(f'{language} does not have a compiler yet')


@dataclass
class CppLinter(Linter):
    language_standard: str
    supported_standards = {'c++', 'c++11', 'c++14', 'c++17', 'c++20'}

    def __post_init__(self):
        if self.language_standard == 'c++':
            self.language_standard = 'c++20'

    def lint(self, submission_paths: list[Path]) -> RunResult:
        submission_paths_str = ' '.join([str(path) for path in submission_paths])

        # Clang Tidy checks
        check_flags = [
            'bugprone-argument-comment',
            'bugprone-assert-side-effect',
            'bugprone-bad-signal-to-kill-thread',
            'bugprone-branch-clone',
            'bugprone-copy-constructor-init',
            'bugprone-dangling-handle',
            'bugprone-dynamic-static-initializers',
            'bugprone-fold-init-type',
            'bugprone-forward-declaration-namespace',
            'bugprone-forwarding-reference-overload',
            'bugprone-inaccurate-erase',
            'bugprone-incorrect-roundings',
            'bugprone-integer-division',
            'bugprone-lambda-function-name',
            'bugprone-macro-parentheses',
            'bugprone-macro-repeated-side-effects',
            'bugprone-misplaced-operator-in-strlen-in-alloc',
            'bugprone-misplaced-pointer-arithmetic-in-alloc',
            'bugprone-misplaced-widening-cast',
            'bugprone-move-forwarding-reference',
            'bugprone-multiple-statement-macro',
            'bugprone-no-escape',
            'bugprone-not-null-terminated-result',
            'bugprone-parent-virtual-call',
            'bugprone-posix-return',
            'bugprone-reserved-identifier',
            'bugprone-sizeof-container',
            'bugprone-sizeof-expression',
            'bugprone-spuriously-wake-up-functions',
            'bugprone-string-constructor',
            'bugprone-string-integer-assignment',
            'bugprone-string-literal-with-embedded-nul',
            'bugprone-suspicious-enum-usage',
            'bugprone-suspicious-include',
            'bugprone-suspicious-memset-usage',
            'bugprone-suspicious-missing-comma',
            'bugprone-suspicious-semicolon',
            'bugprone-suspicious-string-compare',
            'bugprone-swapped-arguments',
            'bugprone-terminating-continue',
            'bugprone-throw-keyword-missing',
            'bugprone-too-small-loop-variable',
            'bugprone-undefined-memory-manipulation',
            'bugprone-undelegated-constructor',
            'bugprone-unhandled-self-assignment',
            'bugprone-unused-raii',
            'bugprone-unused-return-value',
            'bugprone-use-after-move',
            'bugprone-virtual-near-miss',
            'cert-dcl21-cpp',
            'cert-dcl58-cpp',
            'cert-err34-c',
            'cert-err52-cpp',
            'cert-err58-cpp',
            'cert-err60-cpp',
            'cert-flp30-c',
            'cert-msc50-cpp',
            'cert-msc51-cpp',
            'cert-str34-c',
            'cppcoreguidelines-interfaces-global-init',
            'cppcoreguidelines-pro-type-static-cast-downcast',
            'cppcoreguidelines-slicing',
            'google-default-arguments',
            'google-explicit-constructor',
            'google-runtime-operator',
            'hicpp-exception-baseclass',
            'hicpp-multiway-paths-covered',
            'misc-misplaced-const',
            'misc-new-delete-overloads',
            'misc-no-recursion',
            'misc-non-copyable-objects',
            'misc-throw-by-value-catch-by-reference',
            'misc-unconventional-assign-operator',
            'misc-uniqueptr-reset-release',
            'modernize-avoid-bind',
            'modernize-concat-nested-namespaces',
            'modernize-deprecated-headers',
            'modernize-deprecated-ios-base-aliases',
            'modernize-make-shared',
            'modernize-make-unique',
            'modernize-pass-by-value',
            'modernize-raw-string-literal',
            'modernize-redundant-void-arg',
            'modernize-replace-auto-ptr',
            'modernize-replace-disallow-copy-and-assign-macro',
            'modernize-replace-random-shuffle',
            'modernize-return-braced-init-list',
            'modernize-shrink-to-fit',
            'modernize-unary-static-assert',
            'modernize-use-auto',
            'modernize-use-bool-literals',
            'modernize-use-emplace',
            'modernize-use-equals-default',
            'modernize-use-equals-delete',
            'modernize-use-nodiscard',
            'modernize-use-noexcept',
            'modernize-use-nullptr',
            'modernize-use-override',
            'modernize-use-transparent-functors',
            'modernize-use-uncaught-exceptions',
            'mpi-buffer-deref',
            'mpi-type-mismatch',
            'openmp-use-default-none',
            'performance-faster-string-find',
            'performance-for-range-copy',
            'performance-implicit-conversion-in-loop',
            'performance-inefficient-algorithm',
            'performance-inefficient-string-concatenation',
            'performance-inefficient-vector-operation',
            'performance-move-const-arg',
            'performance-move-constructor-init',
            'performance-no-automatic-move',
            'performance-noexcept-move-constructor',
            'performance-trivially-destructible',
            'performance-type-promotion-in-math-fn',
            'performance-unnecessary-copy-initialization',
            'performance-unnecessary-value-param',
            'portability-simd-intrinsics',
            'readability-avoid-const-params-in-decls',
            'readability-const-return-type',
            'readability-container-size-empty',
            'readability-convert-member-functions-to-static',
            'readability-delete-null-pointer',
            'readability-deleted-default',
            'readability-inconsistent-declaration-parameter-name',
            'readability-make-member-function-const',
            'readability-misleading-indentation',
            'readability-misplaced-array-index',
            'readability-non-const-parameter',
            'readability-redundant-control-flow',
            'readability-redundant-declaration',
            'readability-redundant-function-ptr-dereference',
            'readability-redundant-smartptr-get',
            'readability-redundant-string-cstr',
            'readability-redundant-string-init',
            'readability-simplify-subscript-expr',
            'readability-static-accessed-through-instance',
            'readability-static-definition-in-anonymous-namespace',
            'readability-string-compare',
            'readability-uniqueptr-delete-release',
            'readability-use-anyofallof',
        ]
        check_flags = ','.join(check_flags)

        print(f'Linting {len(submission_paths)} files...')
        lint_res = Process(
            f'clang-tidy -warnings-as-errors=* -checks=-*,{check_flags} '
            f'{submission_paths_str} -- -std={self.language_standard}',
            timeout=100, memory_limit_mb=512
        ).run()

        # Remove standard clang-tidy "System warnings removed" message
        warning_message = 'Use -system-headers to display errors from system headers as well.\n'
        if lint_res.errors and warning_message in lint_res.errors:
            lint_res.errors = lint_res.errors[lint_res.errors.index(warning_message) + len(warning_message):].strip()

        if lint_res.errors:
            lint_res.status = Status.LINTING_ERROR
        print('Clang tidy res:', lint_res)
        if lint_res.status != Status.OK:
            return lint_res

        # Clang Format checks
        style = '{BasedOnStyle: llvm, IndentWidth: 4, SortIncludes: false}'
        lint_res = Process(
            f'clang-format --style="{style}" --dry-run --Werror {submission_paths_str}',
            timeout=100, memory_limit_mb=512
        ).run()
        if lint_res.errors:
            lint_res.status = Status.LINTING_ERROR

        print('Clang format res:', lint_res)
        return lint_res
