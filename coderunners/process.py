import errno
import fcntl
import resource
import subprocess
import sys
import time
from dataclasses import dataclass, field
from threading import Thread
from typing import Iterable, Union

import psutil

from models import RunResult, Status


def limit_resources(max_bytes: int):
    max_vm_bytes = 1500 * 1024 * 1024  # 1500 MB
    hard_limit = min(2 * max_vm_bytes, max_vm_bytes)

    resource.setrlimit(resource.RLIMIT_RSS, (max_bytes, hard_limit))
    # The rest are commented as they kill the process with exit code 1
    #   and do not allow to properly handle the memory limit error
    # resource.setrlimit(resource.RLIMIT_DATA, (max_bytes, max_bytes))
    # resource.setrlimit(resource.RLIMIT_AS, (hard_limit, hard_limit))


def send_input(process: subprocess.Popen, inputs: str):
    inputs += '' if inputs.endswith('\n') else '\n'
    process.stdin.write(inputs)
    process.stdin.flush()


@dataclass
class Process:
    command: Union[str, Iterable[str]]
    timeout: float
    memory_limit_mb: int
    output_limit_mb: float = 1
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

        try:
            self.p = subprocess.Popen(
                self.command, shell=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                preexec_fn=lambda: limit_resources(max_bytes=self.memory_limit),
            )
            # TODO: Update this to pipesize=1024*1024 when upgrading to Python 3.10
            #  Ref: https://github.com/MartinXPN/LambdaJudge/issues/50#issuecomment-1080488293
            fcntl.fcntl(self.p.stdin, 1031, 1024 * 1024)
            fcntl.fcntl(self.p.stdout, 1031, 1024 * 1024)
            fcntl.fcntl(self.p.stderr, 1031, 1024 * 1024)
            self.execution_state = True

            # Write to stdin in a separate thread to avoid locking the main program
            input_thread = Thread(target=send_input, args=(self.p, program_input))
            input_thread.start()

            # poll as often as possible; otherwise the subprocess might
            # "sneak" in some extra memory usage while you aren't looking
            while self.finish_time - self.start_time < self.timeout and self.poll():
                time.sleep(self.timeout / 500)
                if self.max_rss_memory > self.memory_limit:
                    status = Status.MLE
                    break
            input_thread.join(timeout=self.timeout / 100)
        except Exception as e:
            print('Program execution resulted in an error:', e)
            status = Status.RUNTIME_ERROR
        finally:
            self.close(kill=True)   # make sure that we don't leave the process dangling
            self.p.stdout.flush()
            self.p.stderr.flush()
            outs, errs = self.p.stdout.read(self.output_limit + 1), self.p.stderr.read(self.output_limit + 1)

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

    def poll(self):
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

    def is_running(self):
        return psutil.pid_exists(self.p.pid) and self.p.poll() is None

    def check_execution_state(self):
        if not self.execution_state:
            return False
        if self.is_running():
            return True

        self.execution_state = False
        self.finish_time = time.time()
        return False

    def close(self, kill=False):
        try:
            pp = psutil.Process(self.p.pid)
            if kill:
                pp.kill()
                self.p.kill()
            else:
                pp.terminate()
        except psutil.NoSuchProcess:
            ...


if __name__ == '__main__':
    res = Process('sleep 7', timeout=5, memory_limit_mb=512).run()
    print(res)
