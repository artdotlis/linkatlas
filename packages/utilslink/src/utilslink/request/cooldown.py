from dataclasses import dataclass
from multiprocessing.synchronize import Lock
from typing import Protocol


class ValueP[T](Protocol):
    @property
    def value(self) -> T: ...
    @value.setter
    def value(self, value: T) -> None: ...


@dataclass(slots=True, frozen=True)
class CoolDown:
    lock: Lock
    last_request: ValueP[float]
    day_request: ValueP[float]
    counter: ValueP[float]

    def _get_per_day_limit(self, time: float, /) -> float:
        wait_time = 0.0
        with self.lock:
            cnt = self.counter.value + 1
            if cnt > 80_000:
                cnt = 0
                wait_time = 86400 - (time - self.day_request.value)
                self.day_request.value = time + wait_time
            self.counter.value = cnt
        return wait_time

    def get_wait_time(self, time: float, /) -> float:
        day_limit = self._get_per_day_limit(time)
        if day_limit > 0:
            return day_limit
        with self.lock:
            wait_time = 0.25 - (time - self.last_request.value)
            self.last_request.value = time
            if wait_time < 0:
                return 0
            if wait_time > 1:
                return 1
            return wait_time
