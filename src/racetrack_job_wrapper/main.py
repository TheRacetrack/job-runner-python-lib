import argparse
import sys

from racetrack_job_wrapper.server import run_configured_entrypoint
from racetrack_job_wrapper.template import render_template
from racetrack_job_wrapper.log.logs import configure_logs, get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser('run', help='run wrapped entrypoint in a server')
    subparser.add_argument(
        'entrypoint_path', default='', nargs='?', help='path to a Python file with an entrypoint class'
    )
    subparser.add_argument('entrypoint_classname', default='', nargs='?')
    subparser.add_argument('--port', type=int, default=None, nargs='?', help='HTTP port to run the server on')
    subparser.set_defaults(func=run_entrypoint)

    subparser = subparsers.add_parser('template', help='Render template file with Manifest variables')
    subparser.add_argument('template_file', help='path to a template file')
    subparser.add_argument('out_file', help='path to a output file')
    subparser.set_defaults(func=_render_template)

    if len(sys.argv) > 1:
        configure_logs(log_level='debug')
        args: argparse.Namespace = parser.parse_args()
        args.func(args)
    else:
        parser.print_help(sys.stderr)


def run_entrypoint(args: argparse.Namespace):
    """Load entrypoint class and run it embedded in a HTTP server"""
    http_port = args.port or 7000
    run_configured_entrypoint(http_port, args.entrypoint_path, args.entrypoint_classname)


def _render_template(args: argparse.Namespace):
    """Render template file with Manifest variables"""
    render_template(args.template_file, args.out_file)
