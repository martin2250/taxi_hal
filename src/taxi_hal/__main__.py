import argparse
import logging

from .commands import commands

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subparser')

    for name, command in commands.items():
        subparser = subparsers.add_parser(name)
        command.build_parser(subparser)

    args = parser.parse_args()

    if not args.subparser:
        parser.print_usage()
        exit(1)

    command = commands[args.subparser]
    success = command.run(**vars(args))
    if not success:
        exit(1)

if __name__ == '__main__':
    main()
