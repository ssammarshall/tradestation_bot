from abc import ABC, abstractmethod
from logging import Logger, getLogger

from app.schemas.bars import Bar, BarHistoryParams, BarHistoryRequest
from app.schemas.signals import EntrySignal


class BaseSetup(ABC):
    def __init__(self, symbol: str, risk_reward_ratio: float = 1.0) -> None:
        self.symbol: str = symbol
        self.risk_reward_ratio: float = risk_reward_ratio
        self.pending_request: BarHistoryRequest | None = None
        self.pending_signal: EntrySignal | None = None
        self.log: Logger = getLogger(self.__class__.__name__)

    @abstractmethod
    def history_params(self) -> BarHistoryParams: ...

    @abstractmethod
    def startup(self, bars: list[Bar]) -> None: ...

    @abstractmethod
    def is_valid(self, bar: Bar) -> bool: ...

    def receive_bars(self, bars: list[Bar]) -> None:
        pass

    def consume_request(self) -> BarHistoryRequest | None:
        request = self.pending_request
        self.pending_request = None
        return request

    def consume_signal(self) -> EntrySignal | None:
        signal = self.pending_signal
        self.pending_signal = None
        return signal

    def reset(self) -> None:
        self.pending_request = None
        self.pending_signal = None
