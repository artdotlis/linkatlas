import argparse
from pathlib import Path
import sys
from saim.shared.parse.date import get_date, date_to_str
from publink.manager.manager import PubReportManager


def _parse_args(argv: list[str], /) -> tuple[str, str, str, str]:
    parser = argparse.ArgumentParser(description="Report strains in online publications")
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
    parser.add_argument(
        "-r",
        "--date",
        action="store",
        default="",
        type=str,
        required=False,
        help="the earliest report date, everything older will be ignored",
        dest="date",
        metavar="str",
    )
    parser.add_argument(
        "-a",
        "--acr",
        action="store",
        default="",
        type=str,
        required=False,
        help="the acronym to report on",
        dest="acr",
        metavar="str",
    )
    args = parser.parse_args(argv)
    return str(args.dir), str(args.include), str(args.date), str(args.acr)


def run() -> None:
    dip, inc, dat, acr = _parse_args(sys.argv[1:])
    working_dir = Path(dip)
    include = Path(inc)
    include_list: Path | None = None
    report_date = get_date(dat)
    if not (working_dir.exists() and working_dir.is_dir()):
        print("Please provide an existing working directory!")
        exit(1)
    if include.exists() and include.is_file():
        include_list = include
    manager = PubReportManager(working_dir)
    manager.report(acr, date_to_str(report_date, True), include_list)
    manager.close()


if __name__ == "__main__":
    run()
