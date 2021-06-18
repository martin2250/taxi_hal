import argparse
import logging
import sys
import time

from .commands import commands

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subparser')

    for name, command in commands.items():
        subparser = subparsers.add_parser(name)
        command.build_parser(subparser)

    args = parser.parse_args()

    command = commands[args.subparser]
    success = command.run(**vars(args))
    if not success:
        exit(1)
