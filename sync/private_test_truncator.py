from dataclasses import dataclass


@dataclass
class PrivateTestTruncator:
    char_count: int = 100

    def truncate(self, tests: list[dict[str, str]]) -> list[dict[str, str]]:
        return [self._truncate_test(test) for test in tests]

    def _truncate_test(self, test: dict[str, str]) -> dict[str, str]:
        return {'input': self._truncate_value(test['input']), 'target': self._truncate_value(test['target'])}

    def _truncate_value(self, value: str) -> str:
        return value[:min(len(value), self.char_count)]
