import sys
from pathlib import Path

import argparse
from seqlink.manager.manager import SeqUpdateManager
from utilslink.configs.agent import create_agent_config


def _parse_args(argv: list[str], /) -> tuple[str, str, int]:
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
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=True,
        dest="conf",
    )
    args = parser.parse_args(argv)
    return str(args.dir), str(args.conf), int(args.worker)


def run() -> None:
    dir_p, conf, worker = _parse_args(sys.argv[1:])
    working_dir = Path(dir_p)
    if not (working_dir.exists() and working_dir.is_dir()):
        print("Please provide an existing working directory!")
        exit(1)
    agent = create_agent_config(Path(conf))
    manager = SeqUpdateManager(working_dir, worker, agent)
    manager.update_database()


if __name__ == "__main__":
    run()
