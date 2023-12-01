from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import sqlite3

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
            print('Creating file at:', self.ROOT / filename)
            (self.ROOT / filename).write_text(content)
        for filename, content in (test.input_assets or {}).items():
            print('Creating asset at:', self.ROOT / filename)
            (self.ROOT / filename).write_bytes(content)

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
            if (self.ROOT / filename).exists():
                print('Removing file at:', self.ROOT / filename)
                (self.ROOT / filename).unlink()


@dataclass
class SQLiteExecutor(Executor):
    script: str
    db_name: str = 'main.db'

    def __post_init__(self):
        self.db = sqlite3.connect(self.db_name)

    def __del__(self):
        self.db.close()

    def run(self, test: TestCase, **kwargs) -> RunResult:
        """
        self.script is the SQL script that needs to be run on the database
        test.input is the initialization SQL script
        test.input_files are all the tables that need to be populated
        test.target is the expected output of the SQL script (can be empty)
        test.target_files are all the tables that need to be populated by the SQL script
        """
        import pandas as pd
        cursor = self.db.cursor()
        cursor.executescript(test.input)

        for filename, content in (test.input_files or {}).items():
            # Load the content of the file into a dataframe and then load it into the db (filename)
            print('Creating table:', filename)
            csv_data = StringIO(content)
            df = pd.read_csv(csv_data)
            print(df.head())
            df.to_sql(filename, self.db, if_exists='replace', index=False)
            print('--- Done ---')

        self.db.commit()

        # Execute the self.script as a single command and get the output
        print('Executing script:', self.script)
        res = pd.read_sql_query(self.script, self.db).to_string(header=False, index=False)
        print('Result:', res)

        r = RunResult(
            status=Status.OK, memory=0, time=0, return_code=0, outputs=res,
            output_files={
                filename: pd.read_sql_query(f'SELECT * FROM {filename}', self.db).to_string()
                for filename in (test.target_files or {}).keys()
            })

        cursor.close()
        return r

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
