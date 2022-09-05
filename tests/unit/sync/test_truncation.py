import pytest

from models import TestCase
from sync.summary import truncate


class TestTruncation:
    @classmethod
    def _get_tests_with_len(cls, char_count: int) -> list[TestCase]:
        data = 'a' * char_count
        test = TestCase(input=data, target=data)
        return [test for _ in range(3)]

    def test_truncated_tests(self):
        tests = self._get_tests_with_len(120)
        truncated_tests = self._get_tests_with_len(90)
        assert truncate(tests, max_len=90) == truncated_tests

    def test_unsupported_type(self):
        with pytest.raises(ValueError):
            # noinspection PyTypeChecker
            truncate(100, 100)
