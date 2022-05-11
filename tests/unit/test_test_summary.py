from unittest import mock

import pytest

from sync.test_summary import SummaryTable, SummaryWriteError, truncate


class TestSummaryTable:
    @mock.patch.object(SummaryTable, '__init__', lambda *args, **kwargs: None)
    def test_summarize_error(self):
        mock_table = mock.MagicMock()
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 404}}
        with pytest.raises(SummaryWriteError):
            # noinspection PyArgumentList
            summary = SummaryTable()
            summary.table = mock_table
            summary.write(problem_id='id', tests=[{'input': 'abc', 'target': 'cba'}])
        mock_table.put_item.assert_called_once()


class TestTruncation:
    @classmethod
    def _get_tests_with_len(cls, char_count: int) -> list[dict[str, str]]:
        data = 'a' * char_count
        test = {'input': data, 'target': data}
        return [dict(test) for _ in range(3)]

    def test_truncated_tests(self):
        tests = self._get_tests_with_len(120)
        truncated_tests = self._get_tests_with_len(90)
        assert truncate(tests, max_len=90) == truncated_tests

    def test_unsupported_type(self):
        with pytest.raises(ValueError):
            # noinspection PyTypeChecker
            truncate(100, 100)
