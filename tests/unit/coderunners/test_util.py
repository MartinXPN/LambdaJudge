from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from coderunners import util


class TestUtil:
    def test_is_float(self):
        assert util.is_float('3.4') is True
        assert util.is_float('not float') is False
        assert util.is_float('NaN') is True
        assert util.is_float('4') is True

    def test_save_code(self):
        code = {
            'main.cpp': 'File 1',
            'another.cpp': 'File 2',
            'dir': {
                'third.cpp': 'File 3'
            },
            'dir2': {
                'four.txt': 'File 4',
                'five.txt': 'File 5',
                'six.txt': 'File 6',
            },
        }
        with TemporaryDirectory() as save_dir:
            save_dir = Path(save_dir)
            saved_paths = util.save_code(save_dir, code)
            assert saved_paths == [
                save_dir / 'main.cpp', save_dir / 'another.cpp',
                save_dir / 'dir' / 'third.cpp',
                save_dir / 'dir2' / 'four.txt', save_dir / 'dir2' / 'five.txt', save_dir / 'dir2' / 'six.txt',
            ]

            # Assert the files have been created successfully
            with open(save_dir / 'main.cpp') as f:
                assert f.read() == 'File 1'
            with open(save_dir / 'another.cpp') as f:
                assert f.read() == 'File 2'
            with open(save_dir / 'dir' / 'third.cpp') as f:
                assert f.read() == 'File 3'
            with open(save_dir / 'dir2' / 'four.txt') as f:
                assert f.read() == 'File 4'
            with open(save_dir / 'dir2' / 'five.txt') as f:
                assert f.read() == 'File 5'
            with open(save_dir / 'dir2' / 'six.txt') as f:
                assert f.read() == 'File 6'

            # Assert that redundant files do not exist
            assert not (save_dir / 'hello.py').exists()
            assert not (save_dir / 'main.cpp').is_dir()
            assert (save_dir / 'dir').is_dir()
            assert (save_dir / 'dir2').is_dir()
            assert (save_dir / 'dir2' / 'five.txt').exists()

    def test_save_code_fails(self):
        """ Anything other than string: string, string: list[list | dict], or string: dict should fail """
        code = {'hello.py': ['something', 'something else']}
        with pytest.raises(TypeError):
            with TemporaryDirectory() as save_dir:
                save_dir = Path(save_dir)
                # noinspection PyTypeChecker
                util.save_code(save_dir, code)

    def test_return_code_to_status(self):
        assert util.return_code2status.get(137) == 'SIGKILL'
