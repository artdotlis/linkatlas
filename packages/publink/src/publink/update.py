import argparse
from pathlib import Path
import sys

from publink.manager.manager import PubUpdateManager
from utilslink.configs.agent import create_agent_config


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
        "-c",
        "--config",
        type=str,
        required=True,
        dest="conf",
    )
    args = parser.parse_args(argv)
    return str(args.dir), int(args.worker), str(args.conf)


def run() -> None:
    dir_p, worker, conf = _parse_args(sys.argv[1:])
    working_dir = Path(dir_p)
    if not (working_dir.exists() and working_dir.is_dir()):
        print("Please provide an existing working directory!")
        exit(1)
    agent = create_agent_config(Path(conf))
    manager = PubUpdateManager(agent, working_dir, worker)
    manager.update_database()


if __name__ == "__main__":
    run()
