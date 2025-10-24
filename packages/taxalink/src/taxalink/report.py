from saim.shared.parse.date import get_date, date_to_str
import argparse
import sys
from pathlib import Path
from taxalink.manager.manager import TaxaReportManager


def _parse_args(argv: list[str], /) -> tuple[str, str, str, str, bool]:
    parser = argparse.ArgumentParser(description="Report type strains in taxonomy data")
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
        "--src_db",
        action="store",
        default="",
        type=str,
        required=False,
        help="the taxonomy source database",
        dest="database",
        metavar="str",
    )
    parser.add_argument(
        "--rank",
        action="store",
        default="",
        type=str,
        required=False,
        help="the taxonomy rank",
        dest="rank",
        metavar="str",
    )
    parser.add_argument(
        "--correct",
        action="store_true",
        help="whether to only report about correct taxonomy names",
        dest="correct",
    )
    args = parser.parse_args(argv)
    return (
        str(args.dir),
        str(args.date),
        str(args.database),
        str(args.rank),
        bool(args.correct),
    )


def run() -> None:
    dir_p, dat, source, rank, correct_only = _parse_args(sys.argv[1:])
    working_dir = Path(dir_p)
    report_date = get_date(dat)
    if not (working_dir.exists() and working_dir.is_dir()):
        print("Please provide an existing working directory!")
        exit(1)
    manager = TaxaReportManager(working_dir)
    manager.report(source, date_to_str(report_date, True), rank, correct_only)
    manager.close()


if __name__ == "__main__":
    run()
