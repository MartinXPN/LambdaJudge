import resource
import subprocess
import time
from dataclasses import dataclass
from typing import Union, Iterable

import psutil

from models import Status, Stats


@dataclass
class Process:
    command: Union[str, Iterable[str]]
    timeout: float
    memory_limit_mb: int
    p: subprocess.Popen = None
    execution_state: bool = False
    max_vms_memory: float = 0
    max_rss_memory: float = 0
    start_time: float = time.time()
    finish_time: float = time.time()

    def execute(self):
        self.max_vms_memory = 0
        self.max_rss_memory = 0
        self.start_time = time.time()

        memory_bytes = self.memory_limit_mb * 1024 * 1024
        self.p = subprocess.Popen(
            self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        )
        self.execution_state = True

    def run(self) -> Stats:
        try:
            self.execute()
            # poll as often as possible; otherwise the subprocess might
            # "sneak" in some extra memory usage while you aren't looking
            while self.finish_time - self.start_time < self.timeout and self.poll():
                time.sleep(self.timeout / 100)

            outs, errs = self.p.communicate(timeout=self.timeout / 100)
            if outs is not None: outs = outs.decode('utf-8')
            if errs is not None: errs = errs.decode('utf-8')

        except subprocess.TimeoutExpired:
            outs, errs = None, Status.TLE
        except MemoryError:
            outs, errs = None, Status.MLE
        finally:
            # make sure that we don't leave the process dangling?
            self.close(kill=True)

        return Stats(max_rss=self.max_rss_memory / 1024 / 1024,
                     max_vms=self.max_vms_memory / 1024 / 1024,
                     total_time=self.finish_time - self.start_time,
                     return_code=self.p.returncode,
                     outputs=outs,
                     errors=errs)

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
                    pass
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
            else:
                pp.terminate()
        except psutil.NoSuchProcess:
            pass


if __name__ == '__main__':
    proc = Process(['sleep 7'], timeout=5, memory_limit_mb=512)
    res = proc.run()
    print(res)
