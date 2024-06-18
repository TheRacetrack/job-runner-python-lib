import random
from typing import Dict, List


class JobEntrypoint:
    def perform(self) -> float:
        return random.random()

    def metrics(self) -> List[Dict]:
        """Collect current metrics values"""
        return [
            {
                'name': 'job_wasted_seconds',
                'description': 'Seconds you have wasted here',
                'value': 1.2,
            },
            {
                'name': 'job_positives',
                'description': 'Number of positive results',
                'value': 5,
                'labels': {
                    'color': 'blue',
                },
            },
            {
                'name': 'job_zero_value',
                'description': 'Nil',
                'value': 0,
            },
            {
                'name': 'job_null_value',
                'description': 'Nil',
                'value': None,
            },
        ]
