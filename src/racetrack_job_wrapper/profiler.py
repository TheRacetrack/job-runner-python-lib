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
    FLAMEGRAPH_FILENAME = 'memray-flamegraph.html'

    @classmethod
    def is_enabled(cls):
        return is_env_flag_enabled('MEMRAY_PROFILER', 'false')

    @classmethod
    def start(cls):
        if not cls.is_enabled():
            return
        if cls.tracker is not None:
            return
        report_path = Path(cls.REPORT_FILENAME)
        if report_path.is_file():
            logger.warning(f'Deleting previous memory report at {report_path}')
            report_path.unlink()
        cls.tracker = memray.Tracker(report_path)
        cls.tracker.__enter__()
        logger.info('Memory profiler started')

    @classmethod
    def stop(cls):
        if cls.tracker is None:
            return
        cls.tracker.__exit__(None, None, None)
        cls.tracker = None
        logger.info(f'Memory profiler stopped, report saved to {cls.REPORT_FILENAME}')

    @classmethod
    def get_report_bytes(cls) -> bytes:
        report_path = Path(cls.REPORT_FILENAME)
        if not report_path.is_file():
            raise ValueError(f'Memory report not found at {report_path}')
        return report_path.read_bytes()

    @classmethod
    def get_flamegraph_html(cls) -> bytes:
        report_path = Path(cls.REPORT_FILENAME)
        flamegraph_path = Path(cls.FLAMEGRAPH_FILENAME)
        if not report_path.is_file():
            raise ValueError(f'Memory report not found at {report_path}')
        if flamegraph_path.is_file():
            flamegraph_path.unlink()
        shell(f'python -m memray flamegraph -o {flamegraph_path} {report_path}')
        return flamegraph_path.read_bytes()

    @classmethod
    def get_stats_output(cls) -> str:
        report_path = Path(cls.REPORT_FILENAME)
        if not report_path.is_file():
            raise ValueError(f'Memory report not found at {report_path}')
        output = shell_output(f'python -m memray stats {report_path}')
        return output
