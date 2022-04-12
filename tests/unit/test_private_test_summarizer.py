from unittest import mock

import pytest

from sync.private_test_summarizer import (PrivateTestSummarizer,
                                          PrivateTestSummarizerException)
from sync.private_test_truncator import PrivateTestTruncator


class TestPrivateTestSummarizer:
    @mock.patch.object(PrivateTestSummarizer, '__init__', lambda *args, **kwargs: None)
    def test_summarize_error(self):
        mock_table = mock.MagicMock()
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 404}}
        with pytest.raises(PrivateTestSummarizerException):
            logger = PrivateTestSummarizer()
            logger.table = mock_table
            logger.write_to_db(problem_id='id', tests=[{'input': 'abc', 'target': 'cba'}])
        mock_table.put_item.assert_called_once()

    @classmethod
    def _get_tests_with_len(cls, char_count: int) -> list[dict[str, str]]:
        data = 'a' * char_count
        test = {'input': data, 'target': data}
        return [dict(test) for _ in range(3)]

    def test_truncated_tests(self):
        tests = self._get_tests_with_len(120)
        truncated_tests = self._get_tests_with_len(90)

        assert PrivateTestTruncator(char_count=90).truncate(tests) == truncated_tests
