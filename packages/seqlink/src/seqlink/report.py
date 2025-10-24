import argparse
from pathlib import Path
import sys
from seqlink.manager.manager import SeqReportManager


def _parse_args(argv: list[str], /) -> tuple[
    str,
    str,
]:
    parser = argparse.ArgumentParser(
        description="Report strains in the sequence database"
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
        "-i",
        "--include",
        action="store",
        type=str,
        required=False,
        default="",
        help="the include file containing a CCNo list to be included in the report",
        dest="include",
        metavar="str",
    )
    args = parser.parse_args(argv)
    return str(args.dir), str(args.include)


def run() -> None:
    dip, inc = _parse_args(sys.argv[1:])
    working_dir = Path(dip)
    include = Path(inc)
    include_list: Path | None = None
    if not (working_dir.exists() and working_dir.is_dir()):
        print("Please provide an existing working directory!")
        exit(1)
    if include.exists() and include.is_file():
        include_list = include
    manager = SeqReportManager(working_dir)
    manager.report(include_list)
    manager.close()


if __name__ == "__main__":
    run()
