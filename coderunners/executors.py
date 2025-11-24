import sqlite3
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from coderunners.process import Process
from models import RunResult, Status, TestCase


class Executor(ABC):
    """
    Executes a test case and returns the result.
    """

    @abstractmethod
    def run(self, test: TestCase, **kwargs) -> RunResult:
        ...

    def cleanup(self, test: TestCase) -> None:
        ...


@dataclass
class ProcessExecutor(Executor):
    command: str | Iterable[str]
    ROOT: Path = Path('/tmp/')

    def run(self, test: TestCase, time_limit: float, memory_limit_mb: int, output_limit_mb: float) -> RunResult:

        # Crete input files and input assets
        for filename, content in (test.input_files or {}).items():
            file = self.ROOT / filename
            print(f'Creating file at: {file} with content len: {len(content)} of type {type(content)}')
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content)
        for filename, content in (test.input_assets or {}).items():
            file = self.ROOT / filename
            print(f'Creating asset at: {file} with content len: {len(content)} of type {type(content)}')
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(content)

        r = Process(
            self.command,
            timeout=time_limit, memory_limit_mb=memory_limit_mb, output_limit_mb=output_limit_mb,
        ).run(test.input)

        # Read output files and output assets into the result
        r.output_files = {
            filename: (self.ROOT / filename).read_text() if (self.ROOT / filename).exists() else ''
            for filename in (test.target_files or {}).keys()
        }
        r.output_assets = {
            filename: (self.ROOT / filename).read_bytes() if (self.ROOT / filename).exists() else b''
            for filename in (test.target_assets or {}).keys()
        }
        return r

    def cleanup(self, test: TestCase) -> None:
        cleanup_files = (test.input_files or {}).keys() | (test.target_files or {}).keys() | \
                        (test.input_assets or {}).keys() | (test.target_assets or {}).keys()
        for filename in cleanup_files:
            print('Removing file at:', self.ROOT / filename)
            (self.ROOT / filename).unlink(missing_ok=True)


@dataclass
class SQLiteExecutor(Executor):
    script: str
    ROOT: Path = Path('/tmp/')
    db_name: str = 'main.db'

    def __post_init__(self):
        self.db = sqlite3.connect(self.ROOT / self.db_name)

    def __del__(self):
        self.db.close()

    def run(self, test: TestCase, **kwargs) -> RunResult:
        """
        self.script is the SQL script that needs to be run on the database.
        test.input is the initialization SQL script.
        test.input_files are all the tables that need to be populated.
        test.target is the expected output of the SQL script (can be empty).
        test.target_files are all the tables that need to be populated by the SQL script.
        """
        import pandas as pd
        cursor = self.db.cursor()

        try:
            cursor.executescript(test.input)
            self.db.commit()
        except sqlite3.Error as e:
            cursor.close()
            return RunResult(
                status=Status.RUNTIME_ERROR, memory=0, time=0, return_code=0, outputs=None,
                errors=str(e),
            )

        for filename, content in (test.input_files or {}).items():
            # Load the content of the file into a dataframe and then load it into the db (filename)
            try:
                print('Creating table:', filename)
                csv_data = StringIO(content)
                df = pd.read_csv(csv_data)
                print(df.head())
                df.to_sql(filename, self.db, if_exists='replace', index=False)
                print('--- Done ---')
            except (sqlite3.Error, pd.errors.ParserError, pd.errors.DatabaseError, ValueError) as e:
                cursor.close()
                return RunResult(
                    status=Status.RUNTIME_ERROR, memory=0, time=0, return_code=0, outputs=None,
                    errors=str(e),
                )

        self.db.commit()

        # Execute the self.script as a single command and get the output
        try:
            print('Executing script:', self.script)
            if self.script.strip().upper().startswith('SELECT'):
                res = pd.read_sql_query(self.script, self.db).to_csv(index=False)
            else:
                cursor.executescript(self.script)
                self.db.commit()
                res = ''
            print('Result:', res)
        except (sqlite3.Error, pd.errors.ParserError, pd.errors.DatabaseError, ValueError) as e:
            cursor.close()
            return RunResult(
                status=Status.RUNTIME_ERROR, memory=0, time=0, return_code=0, outputs=None,
                errors=str(e),
            )

        # Read output files into the result
        try:
            r = RunResult(
                status=Status.OK, memory=0, time=0, return_code=0, outputs=res,
                output_files={
                    filename: pd.read_sql_query(f'SELECT * FROM {filename}', self.db).to_csv(index=False)
                    for filename in (test.target_files or {}).keys()
                })
            cursor.close()
            return r
        except (sqlite3.Error, pd.errors.ParserError, pd.errors.DatabaseError, ValueError) as e:
            cursor.close()
            return RunResult(
                status=Status.RUNTIME_ERROR, memory=0, time=0, return_code=0, outputs=None,
                errors=str(e),
            )

    def cleanup(self, test: TestCase) -> None:
        """ Drops all the tables in the database """
        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f'Dropping {len(tables)} tables')
        for table_name in tables:
            print('Dropping table:', table_name[0], end='...')
            cursor.execute(f'DROP TABLE {table_name[0]}')
            print('Done')

        print('Saving changes')
        self.db.commit()
        cursor.close()
