from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Final, final, Iterator, Iterable, Any

from mpyflow.shared.container.data import InputData

from publink.model.container.literature import LitUpdatePackage, LitType
from utilslink.iter.pack import package_data
from utilslink.parse.date import conv_to_date_str

_MAIN: Final[str] = "literature"


def read_lit_file_txt(file: Path, /) -> str:
    try:
        with file.open() as fth:
            _ = fth.readline().strip().split(",")
            full_text = " ".join(line.strip() for line in fth)
        return full_text.strip()
    except Exception as exc:
        print(f"Corrupt literature file {exc!s}")
    return ""


def _read_lit_path(file: Path, /) -> tuple[str, str, Path]:
    try:
        with file.open() as fth:
            doi, date = fth.readline().strip().split(",")
        return doi.strip(), conv_to_date_str(date.strip()), file
    except Exception as exc:
        print(f"Corrupt literature file {exc!s}")
    return "", "", file


def read_text_from_literature_dir(dir_p: Path, /) -> Iterable[tuple[str, str, Path]]:
    main_path = dir_p.joinpath(_MAIN)
    if not (main_path.exists() and main_path.is_dir()):
        print("\nNo literature directory provided")
    else:
        for file in dir_p.rglob("*.txt"):
            doi, date, file_p = _read_lit_path(Path(file))
            if doi == "" or date == "":
                continue
            yield doi, date, file_p


@final
class LiteratureReader:
    __slots__ = (
        "__data",
        "__in",
        "__iter",
        "__out",
        "__package_size",
        "__version",
        "__work_dir",
    )

    def __init__(self, work_dir: Path, version: str, package_size: int = 1000, /) -> None:
        super().__init__()
        self.__in = True
        self.__out = False
        self.__iter: Iterator[tuple[LitUpdatePackage, ...]] | None = None
        self.__data: None | tuple[LitUpdatePackage, ...] = None
        self.__version = version
        self.__work_dir = work_dir
        self.__package_size = package_size

    @property
    def iter_data(self) -> Iterator[tuple[LitUpdatePackage, ...]]:
        if self.__iter is None:
            self.__iter = iter(self.synchronize())
        return self.__iter

    def has_input(self) -> bool:
        return self.__in

    def has_output(self) -> bool:
        return self.__out

    def wr_on_close(self) -> None:
        self.backend.close()  # type: ignore

    def on_error(self) -> None:
        self.backend.close()  # type: ignore

    def synchronize(self) -> Iterable[tuple[LitUpdatePackage, ...]]:
        data_gen = (
            LitUpdatePackage(
                version=self.__version,
                txt_typ=LitType.full,
                data=(doi.upper(), date, file_p),
            )
            for doi, date, file_p in read_text_from_literature_dir(self.__work_dir)
            if doi != "" and date != ""
        )
        for package in package_data(
            data_gen, self.__package_size, self.__package_size, lambda _val: 1
        ):
            yield package

    async def read(
        self, _th_exc: ThreadPoolExecutor, /
    ) -> InputData[tuple[LitUpdatePackage, ...]] | None:
        buf = next(self.iter_data, None)
        res = buf
        if self.__data is not None:
            res = self.__data
        self.__data = buf
        if res is None:
            return None
        return InputData(tuple(dat for dat in res))

    async def write(self, _data: Any, _th_exc: ThreadPoolExecutor, /) -> bool:
        raise NotImplementedError("Not implemented")

    async def running(self, _th_exc: ThreadPoolExecutor, _provider_cnt: int, /) -> bool:
        if self.__data is not None:
            return True
        self.__data = next(self.iter_data, None)
        return self.__data is not None
