from unittest import mock

import pytest

from models import TestCase
from sync.test_summary import SummaryTable, SummaryWriteError


class TestSummaryTable:
    @mock.patch.object(SummaryTable, '__init__', lambda *args, **kwargs: None)
    def test_summarize_error(self):
        mock_table = mock.MagicMock()
        mock_table.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 404}}
        with pytest.raises(SummaryWriteError):
            # noinspection PyArgumentList
            summary = SummaryTable()
            summary.table = mock_table
            summary.write(problem_id='id', tests=[TestCase(input='abc', target='cba')])
        assert mock_table.put_item.call_count == 2, 'one for trying, another for putting an error message'
