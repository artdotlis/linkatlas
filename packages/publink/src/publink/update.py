import argparse
from pathlib import Path
import sys

from publink.manager.manager import PubUpdateManager


def _parse_args(argv: list[str], /) -> tuple[str, int, str]:
    parser = argparse.ArgumentParser(
        description="Searches strains in online publications"
    )
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
    parser.add_argument(
        "-m",
        "--mail",
        action="store",
        type=str,
        required=False,
        help="the mail used for API service",
        dest="mail",
        metavar="mail",
        default="",
    )
    args = parser.parse_args(argv)
    return str(args.dir), int(args.worker), str(args.mail)


def run() -> None:
    dir_p, worker, mail = _parse_args(sys.argv[1:])
    working_dir = Path(dir_p)
    if not (working_dir.exists() and working_dir.is_dir()):
        print("Please provide an existing working directory!")
        exit(1)
    manager = PubUpdateManager(mail, working_dir, worker)
    manager.update_database()


if __name__ == "__main__":
    run()
