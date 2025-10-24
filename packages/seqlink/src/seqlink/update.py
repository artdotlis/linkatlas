import sys
from pathlib import Path

import argparse
from seqlink.manager.manager import SeqUpdateManager


def _parse_args(argv: list[str], /) -> tuple[str, int]:
    parser = argparse.ArgumentParser(description="Searches strains in sequence data")
    parser.add_argument(
        "-d",
        "--dir",
        action="store",
        type=str,
        required=True,
        help="the input directory containing all sqlite databases",
        dest="dir",
        metavar="str",
    )
    parser.add_argument(
        "-w",
        "--worker",
        action="store",
        type=int,
        required=False,
        default=1,
        help="the worker number to run concurrently",
        dest="worker",
        metavar="int",
    )
    args = parser.parse_args(argv)
    return str(args.dir), int(args.worker)


def run() -> None:
    dir_p, worker = _parse_args(sys.argv[1:])
    working_dir = Path(dir_p)
    if not (working_dir.exists() and working_dir.is_dir()):
        print("Please provide an existing working directory!")
        exit(1)
    manager = SeqUpdateManager(working_dir, worker)
    manager.update_database()


if __name__ == "__main__":
    run()
