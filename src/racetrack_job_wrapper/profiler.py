from typing import Optional
from pathlib import Path

import memray

from racetrack_job_wrapper.log.logs import get_logger
from racetrack_job_wrapper.utils.shell import shell, shell_output
from racetrack_job_wrapper.utils.env import is_env_flag_enabled

logger = get_logger(__name__)


class MemoryProfiler:
    tracker: Optional[memray.Tracker] = None
    REPORT_FILENAME = 'memray-report.bin'
    REPORT_FILE_PATH = Path('/tmp/racetrack-memray-report.bin')
    FLAMEGRAPH_FILENAME = 'memray-flamegraph.html'
    FLAMEGRAPH_FILE_PATH = Path('/tmp/racetrack-memray-flamegraph.html')

    @classmethod
    def is_enabled(cls):
        return is_env_flag_enabled('MEMRAY_PROFILER', 'false')

    @classmethod
    def start(cls):
        if not cls.is_enabled():
            return
        if cls.tracker is not None:
            return
        if cls.REPORT_FILE_PATH.is_file():
            logger.warning(f'Deleting previous memory report at {cls.REPORT_FILE_PATH}')
            cls.REPORT_FILE_PATH.unlink()
        cls.tracker = memray.Tracker(cls.REPORT_FILE_PATH)
        cls.tracker.__enter__()
        logger.info('Memory profiler started')

    @classmethod
    def stop(cls):
        if cls.tracker is None:
            return
        cls.tracker.__exit__(None, None, None)
        cls.tracker = None
        logger.info(f'Memory profiler stopped, report saved to {cls.REPORT_FILE_PATH}')

    @classmethod
    def get_report_bytes(cls) -> bytes:
        if not cls.REPORT_FILE_PATH.is_file():
            raise ValueError(f'Memory report not found at {cls.REPORT_FILE_PATH}')
        return cls.REPORT_FILE_PATH.read_bytes()

    @classmethod
    def get_flamegraph_html(cls) -> bytes:
        if not cls.REPORT_FILE_PATH.is_file():
            raise ValueError(f'Memory report not found at {cls.REPORT_FILE_PATH}')
        if cls.FLAMEGRAPH_FILE_PATH.is_file():
            cls.FLAMEGRAPH_FILE_PATH.unlink()
        shell(f'python -m memray flamegraph -o {cls.FLAMEGRAPH_FILE_PATH} {cls.REPORT_FILE_PATH}')
        return cls.FLAMEGRAPH_FILE_PATH.read_bytes()

    @classmethod
    def get_stats_output(cls) -> str:
        if not cls.REPORT_FILE_PATH.is_file():
            raise ValueError(f'Memory report not found at {cls.REPORT_FILE_PATH}')
        output = shell_output(f'python -m memray stats {cls.REPORT_FILE_PATH}')
        return output
