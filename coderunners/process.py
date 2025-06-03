import errno
import os
import resource
import signal
import subprocess
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from threading import Thread

import psutil

from models import RunResult, Status


@dataclass
class Outputs:
    stdout: str = ''
    stderr: str = ''


def limit_resources(max_bytes: int):
    max_vm_bytes = 1500 * 1024 * 1024  # 1500 MB
    hard_limit = min(2 * max_vm_bytes, max_vm_bytes)

    resource.setrlimit(resource.RLIMIT_RSS, (max_bytes, hard_limit))
    # The rest are commented as they kill the process with exit code 1
    #   and do not allow to properly handle the memory limit error
    # resource.setrlimit(resource.RLIMIT_DATA, (max_bytes, max_bytes))
    # resource.setrlimit(resource.RLIMIT_AS, (hard_limit, hard_limit))


def send_input(process: subprocess.Popen, inputs: str) -> None:
    process.stdin.write(inputs)
    process.stdin.flush()
    process.stdin.close()


CHUNK_SIZE = 2 ** 20  # Make sure we don't read slower than the program prints


def read_stdout(process: subprocess.Popen, res: Outputs) -> None:
    while True:
        process.stdout.flush()
        chunk = process.stdout.read(CHUNK_SIZE)
        if chunk == '' and process.poll() is not None:
            break
        res.stdout += chunk


def read_stderr(process: subprocess.Popen, res: Outputs) -> None:
    while True:
        process.stderr.flush()
        chunk = process.stderr.read(CHUNK_SIZE)
        if chunk == '' and process.poll() is not None:
            break
        res.stderr += chunk


@dataclass
class Process:
    command: str | Iterable[str]
    timeout: float
    memory_limit_mb: int
    output_limit_mb: float = 1
    cwd: Path = Path('/tmp/')
    p: subprocess.Popen = None
    execution_state: bool = False
    max_vms_memory: float = 0
    max_rss_memory: float = 0
    start_time: float = time.time()
    finish_time: float = time.time()
    memory_limit: int = field(init=False)
    output_limit: int = field(init=False)

    def __post_init__(self):
        self.memory_limit = self.memory_limit_mb * 1024 * 1024
        self.output_limit = int(self.output_limit_mb * 1024 * 1024)

    def run(self, program_input: str = '') -> RunResult:
        status = Status.OK
        self.max_vms_memory = 0
        self.max_rss_memory = 0
        self.start_time = time.time()
        outputs = Outputs()

        try:
            self.p = subprocess.Popen(
                self.command,
                shell=True,
                pipesize=1024 * 1024,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=lambda: limit_resources(max_bytes=self.memory_limit),
                cwd=self.cwd,
                start_new_session=True,
            )
            self.execution_state = True

            # Read/write to stdin/stdout/stderr in a separate thread to avoid locking the main program
            input_thread = Thread(target=send_input, args=(self.p, program_input))
            stdout_thread = Thread(target=read_stdout, args=(self.p, outputs))
            stderr_thread = Thread(target=read_stderr, args=(self.p, outputs))
            input_thread.start()
            stdout_thread.start()
            stderr_thread.start()

            # poll as often as possible; otherwise the subprocess might
            # "sneak" in some extra memory usage while you aren't looking
            while self.finish_time - self.start_time < self.timeout and self.poll():
                time.sleep(self.timeout / 500)
                if self.max_rss_memory > self.memory_limit:
                    status = Status.MLE
                    break

            # Cleanup and read the final results
            input_thread.join(timeout=max(self.timeout / 100, 0.01))
            stdout_thread.join(timeout=max(self.timeout / 100, 0.01))
            stderr_thread.join(timeout=max(self.timeout / 100, 0.01))
        except Exception as e:
            print('Program execution resulted in an error:', e)
            status = Status.RUNTIME_ERROR
        finally:
            self.close()   # make sure that we don't leave the process dangling

        # Time/Memory limits + Runtime errors
        if self.finish_time - self.start_time > self.timeout:
            status = Status.TLE
        if self.p.returncode in {errno.ENOMEM, 137}:            # SIGKILL
            status = Status.MLE
        elif self.p.returncode in {139, 143}:                   # SIGSEGV, SIGTERM
            status = Status.RUNTIME_ERROR
        elif self.p.returncode != 0 and status == Status.OK:    # Nonzero return code is a runtime error
            status = Status.RUNTIME_ERROR

        # Output limits
        outs, errs = outputs.stdout, outputs.stderr
        if sys.getsizeof(outs) > self.output_limit:
            status = Status.OLE
            outs = outs[:self.output_limit // 2]
        if sys.getsizeof(errs) > self.output_limit:
            status = Status.OLE
            errs = errs[:self.output_limit // 2]

        return RunResult(
            status=status,
            memory=self.max_rss_memory / 1024 / 1024,
            time=self.finish_time - self.start_time,
            return_code=self.p.returncode or 0,
            outputs=outs, errors=errs,
        )

    def poll(self) -> bool:
        if not self.check_execution_state():
            return False

        self.finish_time = time.time()
        try:
            pp = psutil.Process(self.p.pid)

            # obtain a list of the subprocess and all its descendants
            descendants = list(pp.children(recursive=True))
            descendants = descendants + [pp]

            rss_memory = 0
            vms_memory = 0

            # calculate and sum up the memory of the subprocess and all its descendants
            for descendant in descendants:
                try:
                    mem_info = descendant.memory_info()
                    rss_memory += mem_info[0]
                    vms_memory += mem_info[1]
                except psutil.NoSuchProcess:
                    # sometimes a subprocess descendant will have terminated between the time
                    # we obtain a list of descendants, and the time we actually poll this
                    # descendant's memory usage.
                    ...
            self.max_vms_memory = max(self.max_vms_memory, vms_memory)
            self.max_rss_memory = max(self.max_rss_memory, rss_memory)

        except psutil.NoSuchProcess:
            return self.check_execution_state()

        return self.check_execution_state()

    def is_running(self) -> bool:
        return psutil.pid_exists(self.p.pid) and self.p.poll() is None

    def check_execution_state(self) -> bool:
        if not self.execution_state:
            return False
        if self.is_running():
            return True

        self.execution_state = False
        self.finish_time = time.time()
        return False

    def close(self) -> None:
        try:
            root = psutil.Process(self.p.pid)
            # Kill the whole process group created for the submission
            try:
                os.killpg(os.getpgid(self.p.pid), signal.SIGKILL)
            except OSError:
                ...

            # Explicitly kill all child processes as an extra precaution
            for child in root.children(recursive=True):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    ...

            root.kill()
            self.p.kill()
        except psutil.NoSuchProcess:
            ...
