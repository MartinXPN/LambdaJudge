import copy
from unittest import mock

from sync.private_test_logger import (PrivateTestLogger,
                                      PrivateTestLoggerException)


class TestPrivateTestLogger:
    @mock.patch.object(PrivateTestLogger, '__init__', lambda *args, **kwargs: None)
    def test_log_error(self):
        mock_table = mock.MagicMock()
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 404}}
        try:
            logger = PrivateTestLogger()
            logger.table = mock_table
            logger.log(problem_id='id', tests=[{'input': 'abc', 'target': 'cba'}])
        except PrivateTestLoggerException:
            mock_table.put_item.assert_called_once()
            return

        assert False, 'Exception was not thrown'

    @classmethod
    def _get_tests_with_len(cls, length):
        data = 'a' * length
        test = {'input': data, 'target': data}
        return copy.deepcopy([test] * 3)

    def test_truncated_tests(self):
        tests = self._get_tests_with_len(120)
        truncated_tests = self._get_tests_with_len(100)

        assert PrivateTestLogger.truncated_tests(tests) == truncated_tests
